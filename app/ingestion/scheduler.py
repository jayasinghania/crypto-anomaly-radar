"""
Phase 1 - Task B: Scheduler + retry wrapper.

Calls fetcher.fetch_prices() on a fixed interval, forever, with retry +
exponential backoff on failure so one flaky request doesn't crash the
whole pipeline. Each successful poll is appended to a local JSONL file -
a stand-in for the database Phase 2 will introduce.

Depends on app/ingestion/fetcher.py - merge that PR first, then pull the
updated main before testing this against the real fetcher.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from app.ingestion.fetcher import FetchError, fetch_prices

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ASSETS = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]
POLL_INTERVAL_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2

DATA_FILE = Path("data/ticks.jsonl")


async def fetch_with_retry(assets: list[str]) -> dict | None:
    """
    Call fetch_prices(), retrying on failure with exponential backoff
    (2s, 4s, 8s, ...). Returns None instead of raising if every attempt
    fails, so the scheduling loop can log it and keep running rather
    than crashing.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await fetch_prices(assets)
        except FetchError as exc:
            if attempt == MAX_RETRIES:
                logger.error("Fetch failed after %d attempts: %s", attempt, exc)
                return None
            wait = BACKOFF_BASE_SECONDS**attempt
            logger.warning(
                "Fetch attempt %d/%d failed (%s), retrying in %ds",
                attempt, MAX_RETRIES, exc, wait,
            )
            await asyncio.sleep(wait)
    return None


def write_tick(asset: str, price: float, fetched_at) -> None:
    """Append one price reading to the local JSONL file."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("a") as f:
        f.write(json.dumps({
            "asset": asset,
            "price": price,
            "fetched_at": fetched_at.isoformat(),
        }) + "\n")


async def run_forever() -> None:
    logger.info("Starting ingestion loop: %s every %ds", ASSETS, POLL_INTERVAL_SECONDS)
    while True:
        prices = await fetch_with_retry(ASSETS)
        if prices is not None:
            for asset, data in prices.items():
                write_tick(asset, data["price"], data["fetched_at"])
                logger.info("%s: $%s", asset, data["price"])
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    # Run with: python -m app.ingestion.scheduler   (from the repo root)
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("Stopped.")