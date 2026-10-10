"""Rolling z-score anomaly detection, run against an in-memory database."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.analytics import stats
from app.storage.models import AnomalyEvent, Bar, Metric

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bucket(i: int) -> datetime:
    return START + timedelta(minutes=i)


@pytest.fixture
def factory(db_session_factory, monkeypatch):
    # Point the stats module at the throwaway database instead of Postgres.
    monkeypatch.setattr(stats, "SessionLocal", db_session_factory)
    return db_session_factory


def add_bars(factory, closes, asset="bitcoin"):
    with factory() as session:
        for i, c in enumerate(closes):
            session.add(Bar(asset=asset, bucket_start=bucket(i), open=c, high=c, low=c, close=c))
        session.commit()


def test_unknown_bar_returns_none(factory):
    assert stats.compute_metric_for_bar("bitcoin", bucket(5)) is None


def test_not_enough_history_gives_no_zscore(factory):
    add_bars(factory, [100.0, 101.0])
    metric = stats.compute_metric_for_bar("bitcoin", bucket(1))  # only 1 prior bar
    assert metric.z_score is None
    assert metric.rolling_mean is None
    assert metric.is_anomaly is False


def test_normal_movement_is_not_flagged(factory):
    add_bars(factory, [100.0, 101.0, 99.0, 100.0, 101.0, 99.0, 100.0, 100.5])
    metric = stats.compute_metric_for_bar("bitcoin", bucket(7))
    assert abs(metric.z_score) < stats.Z_THRESHOLD
    assert metric.is_anomaly is False


def test_a_spike_is_flagged_and_the_baseline_excludes_the_current_bar(factory):
    closes = [100.0 + (i % 2) for i in range(20)] + [150.0]  # 100/101 alternating, then a jump
    add_bars(factory, closes)
    metric = stats.compute_metric_for_bar("bitcoin", bucket(20))
    # Prior 20 bars: mean 100.5, std 0.5, so z = (150 - 100.5) / 0.5 = 99.
    # Only a baseline that leaves the spike out can produce this number.
    assert metric.rolling_mean == pytest.approx(100.5)
    assert metric.rolling_std == pytest.approx(0.5)
    assert metric.z_score == pytest.approx(99.0)
    assert metric.is_anomaly is True


def test_flat_history_gives_zero_zscore_not_a_crash(factory):
    add_bars(factory, [100.0] * 5 + [105.0])  # zero variance in the baseline
    metric = stats.compute_metric_for_bar("bitcoin", bucket(5))
    assert metric.z_score == 0.0
    assert metric.is_anomaly is False


def test_save_metric_logs_an_anomaly_exactly_once(factory):
    add_bars(factory, [100.0 + (i % 2) for i in range(20)] + [150.0])
    metric = stats.compute_metric_for_bar("bitcoin", bucket(20))

    stats.save_metric(metric)
    stats.save_metric(metric)  # the worker can re-process a bar; it must not duplicate

    with factory() as session:
        assert len(session.scalars(select(Metric)).all()) == 1
        events = session.scalars(select(AnomalyEvent)).all()
    assert len(events) == 1
    assert events[0].asset == "bitcoin"
    assert events[0].price_at_event == 150.0
    assert events[0].z_score == pytest.approx(99.0)


def test_save_metric_does_not_log_an_event_for_normal_bars(factory):
    add_bars(factory, [100.0, 101.0, 99.0, 100.0, 101.0, 100.5])
    stats.save_metric(stats.compute_metric_for_bar("bitcoin", bucket(5)))

    with factory() as session:
        assert len(session.scalars(select(Metric)).all()) == 1
        assert session.scalars(select(AnomalyEvent)).all() == []
