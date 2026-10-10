"""API endpoints, run against an in-memory database."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.api.main import app
from app.config import ASSETS
from app.storage.models import AnomalyEvent, Bar, Tick

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def factory(db_session_factory):
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield db_session_factory
    app.dependency_overrides.clear()


@pytest.fixture
def client(factory):
    # Deliberately NOT used as a context manager: that would run the app's
    # startup (the Redis listener), and tests must not need Redis.
    return TestClient(app)


def seed_bars(factory, n, asset="bitcoin"):
    with factory() as session:
        for i in range(n):
            c = 100.0 + i  # a perfectly linear price: 100, 101, 102, ...
            session.add(Bar(asset=asset, bucket_start=START + timedelta(minutes=i),
                            open=c, high=c, low=c, close=c))
        session.commit()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_assets_lists_the_tracked_basket(client):
    assert client.get("/assets").json() == ASSETS


def test_unknown_asset_is_a_404(client):
    assert client.get("/bars/notacoin").status_code == 404
    assert client.get("/prices/notacoin").status_code == 404
    assert client.get("/forecast/notacoin").status_code == 404


def test_bars_come_back_newest_first_and_respect_limit(client, factory):
    seed_bars(factory, 5)
    body = client.get("/bars/bitcoin?limit=3").json()
    assert [b["close"] for b in body] == [104.0, 103.0, 102.0]


def test_limit_is_validated(client):
    assert client.get("/bars/bitcoin?limit=0").status_code == 422


def test_prices_newest_first(client, factory):
    with factory() as session:
        for i in range(3):
            session.add(Tick(asset="bitcoin", price=100.0 + i, fetched_at=START + timedelta(seconds=30 * i)))
        session.commit()
    body = client.get("/prices/bitcoin").json()
    assert [t["price"] for t in body] == [102.0, 101.0, 100.0]


def test_anomalies_can_be_filtered_by_asset(client, factory):
    with factory() as session:
        for asset in ("bitcoin", "ethereum"):
            session.add(AnomalyEvent(asset=asset, ts=START, z_score=4.2, price_at_event=1.0))
        session.commit()
    assert len(client.get("/anomalies").json()) == 2
    only_eth = client.get("/anomalies?asset=ethereum").json()
    assert [e["asset"] for e in only_eth] == ["ethereum"]
    assert client.get("/anomalies?asset=notacoin").status_code == 404


def test_forecast_refuses_when_there_is_not_enough_data(client, factory):
    seed_bars(factory, 5)
    response = client.get("/forecast/bitcoin")
    assert response.status_code == 400
    assert "Not enough data" in response.json()["detail"]


def test_forecast_returns_one_point_per_horizon_step(client, factory):
    seed_bars(factory, 30)
    body = client.get("/forecast/bitcoin?horizon=3").json()
    assert body["horizon"] == 3
    assert body["based_on_bars"] == 30
    assert body["last_close"] == 129.0
    # Holt continues a perfectly linear series exactly.
    assert [p["price"] for p in body["forecast"]] == pytest.approx([130.0, 131.0, 132.0])
    # Forecast points are one bar (60 seconds) apart.
    times = [datetime.fromisoformat(p["bar_start"]) for p in body["forecast"]]
    assert [(b - a).total_seconds() for a, b in zip(times, times[1:])] == [60.0, 60.0]


def test_accuracy_compares_holt_against_the_naive_baseline(client, factory):
    seed_bars(factory, 40)
    body = client.get("/forecast/bitcoin/accuracy?horizon=1").json()
    assert body["samples"] == 40 - 10 - 1 + 1
    assert body["holt_mape"] < body["naive_mape"]
    assert body["beats_naive"] is True
