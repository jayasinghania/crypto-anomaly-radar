"""
Phase 3 - Bar aggregation.

Reads raw ticks and rolls them up into fixed-size OHLCV bars per asset.
This module does ONE thing: turn a window of raw ticks into a single bar.
It knows nothing about rolling stats or anomaly detection - that's
stats.py's job, same separation-of-concerns idea as fetcher/scheduler
in Phase 1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.storage.database import SessionLocal
from app.storage.models import Bar, Tick

BAR_INTERVAL_SECONDS = 60


def floor_to_bucket(ts: datetime, interval_seconds: int = BAR_INTERVAL_SECONDS) -> datetime:
    """Round a timestamp down to the start of its bar bucket."""
    epoch = ts.timestamp()
    bucket = epoch - (epoch % interval_seconds)
    return datetime.fromtimestamp(bucket, tz=timezone.utc)


def build_bar_for_asset(asset: str, bucket_start: datetime) -> Bar | None:
    """
    Aggregate raw ticks for one asset within [bucket_start, bucket_start +
    interval) into a single OHLCV bar. Returns None if there were no
    ticks in that window (e.g. the ingestion loop was briefly down).
    """
    bucket_end = bucket_start + timedelta(seconds=BAR_INTERVAL_SECONDS)

    with SessionLocal() as session:
        ticks = session.scalars(
            select(Tick)
            .where(Tick.asset == asset)
            .where(Tick.fetched_at >= bucket_start)
            .where(Tick.fetched_at < bucket_end)
            .order_by(Tick.fetched_at)
        ).all()

        if not ticks:
            return None

        prices = [t.price for t in ticks]
        return Bar(
            asset=asset,
            bucket_start=bucket_start,
            open=prices[0],
            high=max(prices),
            low=min(prices),
            close=prices[-1],
        )


def upsert_bar(bar: Bar) -> None:
    """Insert a bar, or update it in place if one already exists for this asset+bucket."""
    with SessionLocal() as session:
        existing = session.scalar(
            select(Bar)
            .where(Bar.asset == bar.asset)
            .where(Bar.bucket_start == bar.bucket_start)
        )
        if existing:
            existing.open = bar.open
            existing.high = bar.high
            existing.low = bar.low
            existing.close = bar.close
        else:
            session.add(bar)
        session.commit()
