"""
Phase 3 - Analytics worker.

Runs once per bar period: rolls up the latest fully-completed bar for
each tracked asset, computes its rolling stats and anomaly flag, and
persists both. Deliberately a separate process from the ingestion
scheduler - ingestion should never wait on analytics, and analytics
should never wait on ingestion. If this process crashes, price
collection keeps running untouched; you just restart the analytics
worker and it picks back up on the next cycle.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.analytics.aggregator import (
    BAR_INTERVAL_SECONDS,
    build_bar_for_asset,
    floor_to_bucket,
    upsert_bar,
)
from app.analytics.stats import compute_metric_for_bar, save_metric
from app.config import ASSETS
from app.realtime.publisher import publish_anomaly, publish_metric

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def latest_completed_bucket() -> datetime:
    """
    The most recently fully-elapsed bar bucket. We never aggregate the
    bucket that's still filling up, since its "close" price wouldn't
    actually be final yet.
    """
    now = datetime.now(timezone.utc)
    current_bucket = floor_to_bucket(now)
    return current_bucket - timedelta(seconds=BAR_INTERVAL_SECONDS)


def run_cycle() -> list[dict]:
    """
    Runs synchronously in a worker thread (see run_forever below). Returns
    plain dicts, not ORM objects - by the time this function returns, the
    DB sessions used inside it have already closed, and reading an
    attribute off a detached ORM object after that is exactly the
    DetachedInstanceError bug from earlier in Phase 3. Plain values have
    no such problem.
    """
    bucket_start = latest_completed_bucket()
    results: list[dict] = []

    for asset in ASSETS:
        bar = build_bar_for_asset(asset, bucket_start)
        if bar is None:
            logger.info("%s: no ticks in bucket %s, skipping", asset, bucket_start.isoformat())
            continue

        close_price = bar.close
        upsert_bar(bar)

        metric = compute_metric_for_bar(asset, bucket_start)
        if metric is None:
            continue

        is_anomaly = metric.is_anomaly
        z_score = metric.z_score
        save_metric(metric)

        flag = " <-- ANOMALY" if is_anomaly else ""
        z_display = f"{z_score:.2f}" if z_score is not None else "n/a"
        logger.info(
            "%s %s: close=%.2f z=%s%s",
            asset, bucket_start.isoformat(), close_price, z_display, flag,
        )

        results.append({
            "asset": asset,
            "bucket_start": bucket_start,
            "close": close_price,
            "z_score": z_score,
            "is_anomaly": is_anomaly,
        })

    return results


async def run_forever() -> None:
    logger.info("Starting analytics worker: %s every %ds", ASSETS, BAR_INTERVAL_SECONDS)
    while True:
        # run_cycle() does several blocking DB calls - offload the whole
        # cycle to a thread so it can't stall this loop's own timing.
        # Publishing happens out here afterward, back on the event loop,
        # since publish_* are async Redis calls.
        results = await asyncio.to_thread(run_cycle)
        for r in results:
            await publish_metric(r["asset"], r["z_score"], r["is_anomaly"], r["bucket_start"])
            if r["is_anomaly"]:
                await publish_anomaly(r["asset"], r["z_score"], r["close"], r["bucket_start"])
        await asyncio.sleep(BAR_INTERVAL_SECONDS)


if __name__ == "__main__":
    # Run with: python -m app.analytics.worker   (from the repo root,
    # in a SEPARATE terminal from the ingestion scheduler)
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("Stopped.")
