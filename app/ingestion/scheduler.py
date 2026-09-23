"""
Phase 1/2 - Scheduler + retry wrapper.

Calls fetcher.fetch_prices() on a fixed interval, forever, with retry +
exponential backoff on failure so one flaky request doesn't crash the
whole pipeline. Each successful poll is persisted via the storage layer
(Postgres, as of Phase 2) - this module no longer touches the database
directly, it just calls save_tick().

Depends on app/ingestion/fetcher.py and app/storage/repository.py.
"""

from __future__ import annotations

import asyncio
import logging

from app.ingestion.fetcher import FetchError, fetch_prices
from app.storage.repository import save_tick

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ASSETS = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]
POLL_INTERVAL_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2


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


async def run_forever() -> None:
    logger.info("Starting ingestion loop: %s every %ds", ASSETS, POLL_INTERVAL_SECONDS)
    while True:
        prices = await fetch_with_retry(ASSETS)
        if prices is not None:
            for asset, data in prices.items():
                # save_tick() is a blocking (synchronous) DB call - run
                # it in a worker thread so it never stalls the async
                # event loop that's also waiting on the next fetch.
                await asyncio.to_thread(save_tick, asset, data["price"], data["fetched_at"])
                logger.info("%s: $%s", asset, data["price"])
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    # Run with: python -m app.ingestion.scheduler   (from the repo root)
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("Stopped.")
