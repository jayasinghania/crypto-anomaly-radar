"""
Phase 5 - Redis publisher.

Ingestion and analytics call these functions to broadcast events over
Redis pub/sub, without knowing or caring who (if anyone) is listening.
The WebSocket layer subscribes to the same channels and forwards
whatever it receives to connected browser clients. This indirection is
what lets any number of WebSocket connections - or, in principle,
multiple API server processes behind a load balancer - all share one
live feed without ingestion/analytics tracking connections themselves.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

TICKS_CHANNEL = "ticks"
METRICS_CHANNEL = "metrics"
ANOMALIES_CHANNEL = "anomalies"

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def publish_tick(asset: str, price: float, fetched_at: datetime) -> None:
    await get_redis_client().publish(TICKS_CHANNEL, json.dumps({
        "type": "tick",
        "asset": asset,
        "price": price,
        "fetched_at": fetched_at.isoformat(),
    }))


async def publish_metric(asset: str, z_score: float | None, is_anomaly: bool, bucket_start: datetime) -> None:
    await get_redis_client().publish(METRICS_CHANNEL, json.dumps({
        "type": "metric",
        "asset": asset,
        "z_score": z_score,
        "is_anomaly": is_anomaly,
        "bucket_start": bucket_start.isoformat(),
    }))


async def publish_anomaly(asset: str, z_score: float, price: float, ts: datetime) -> None:
    await get_redis_client().publish(ANOMALIES_CHANNEL, json.dumps({
        "type": "anomaly",
        "asset": asset,
        "z_score": z_score,
        "price": price,
        "ts": ts.isoformat(),
    }))
