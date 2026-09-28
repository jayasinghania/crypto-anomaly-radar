"""
Phase 3 - Rolling stats + anomaly detection.

For each new bar, computes a rolling mean/stddev baseline from the N
bars immediately before it, and flags the new bar as anomalous if it
deviates more than Z_THRESHOLD standard deviations from that baseline.

Deliberately plain statistics, not machine learning: a z-score is enough
to catch genuine anomalies, and unlike a black-box model, you can point
to exactly why any single flag fired - "this bar was 3.4 standard
deviations from the trailing 20-bar mean." That's a real, defensible
answer if someone questions your anomaly logic in an interview.
"""

from __future__ import annotations

import statistics
from datetime import datetime

from sqlalchemy import select

from app.storage.database import SessionLocal
from app.storage.models import AnomalyEvent, Bar, Metric

ROLLING_WINDOW = 20
Z_THRESHOLD = 3.0


def compute_metric_for_bar(asset: str, bucket_start: datetime) -> Metric | None:
    """
    Compute rolling mean/std/z-score for one bar, using the ROLLING_WINDOW
    bars immediately before it (never including it) as the baseline.
    """
    with SessionLocal() as session:
        current = session.scalar(
            select(Bar)
            .where(Bar.asset == asset)
            .where(Bar.bucket_start == bucket_start)
        )
        if current is None:
            return None

        history = session.scalars(
            select(Bar)
            .where(Bar.asset == asset)
            .where(Bar.bucket_start < bucket_start)
            .order_by(Bar.bucket_start.desc())
            .limit(ROLLING_WINDOW)
        ).all()

        if len(history) < 2:
            # Not enough history yet for a meaningful baseline - this is
            # expected for the first ~20 minutes after starting the
            # pipeline, not a bug.
            return Metric(
                asset=asset, bucket_start=bucket_start,
                rolling_mean=None, rolling_std=None,
                z_score=None, is_anomaly=False,
            )

        closes = [b.close for b in history]
        mean = statistics.mean(closes)
        std = statistics.pstdev(closes)
        z_score = 0.0 if std == 0 else (current.close - mean) / std

        return Metric(
            asset=asset,
            bucket_start=bucket_start,
            rolling_mean=mean,
            rolling_std=std,
            z_score=z_score,
            is_anomaly=abs(z_score) >= Z_THRESHOLD,
        )


def save_metric(metric: Metric) -> None:
    """Upsert the metric row, and log an anomaly_event if it's flagged."""
    with SessionLocal() as session:
        existing = session.scalar(
            select(Metric)
            .where(Metric.asset == metric.asset)
            .where(Metric.bucket_start == metric.bucket_start)
        )
        if existing:
            existing.rolling_mean = metric.rolling_mean
            existing.rolling_std = metric.rolling_std
            existing.z_score = metric.z_score
            existing.is_anomaly = metric.is_anomaly
        else:
            session.add(metric)
        session.commit()

        if not metric.is_anomaly:
            return

        already_logged = session.scalar(
            select(AnomalyEvent)
            .where(AnomalyEvent.asset == metric.asset)
            .where(AnomalyEvent.ts == metric.bucket_start)
        )
        if already_logged:
            return

        bar = session.scalar(
            select(Bar)
            .where(Bar.asset == metric.asset)
            .where(Bar.bucket_start == metric.bucket_start)
        )
        session.add(AnomalyEvent(
            asset=metric.asset,
            ts=metric.bucket_start,
            z_score=metric.z_score,
            price_at_event=bar.close if bar else 0.0,
        ))
        session.commit()
