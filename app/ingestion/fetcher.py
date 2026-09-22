"""
Phase 1 - Task A: Price fetcher.

Fetches current prices for a basket of crypto assets from the CoinGecko
public API. This module does ONE thing: given a list of asset ids, return
their current prices. It knows nothing about scheduling, retries, or
storage - that's scheduler.py's job. Keeping "do the thing" separate from
"when/how often to do it" is deliberate, and it's what lets the two of
you build this in parallel without stepping on each other.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


class FetchError(Exception):
    """Raised when the price fetch fails for any reason."""


async def fetch_prices(assets: list[str], vs_currency: str = "usd") -> dict[str, dict]:
    """
    Fetch current prices for the given CoinGecko asset ids.

    Args:
        assets: CoinGecko asset ids, e.g. ["bitcoin", "ethereum"].
        vs_currency: the currency to price against, default "usd".

    Returns:
        A dict keyed by asset id, e.g.:
        {
            "bitcoin": {"price": 61234.5, "fetched_at": datetime(...)},
            "ethereum": {"price": 3021.1, "fetched_at": datetime(...)},
        }

    Raises:
        FetchError: if the request fails or the response is malformed.
    """
    params = {
        "ids": ",".join(assets),
        "vs_currencies": vs_currency,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(COINGECKO_URL, params=params)
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPError as exc:
            raise FetchError(f"Request to CoinGecko failed: {exc}") from exc

    fetched_at = datetime.now(timezone.utc)
    result: dict[str, dict] = {}

    for asset in assets:
        if asset not in raw or vs_currency not in raw[asset]:
            # CoinGecko silently omits unknown ids instead of erroring -
            # we turn that into an explicit failure so it's never missed.
            raise FetchError(f"No price returned for asset '{asset}'")
        result[asset] = {
            "price": raw[asset][vs_currency],
            "fetched_at": fetched_at,
        }

    return result


if __name__ == "__main__":
    # Quick manual check: run `python -m app.ingestion.fetcher` from the
    # repo root once httpx is installed. Should print live prices once.
    sample = asyncio.run(fetch_prices(["bitcoin", "ethereum"]))
    for asset, data in sample.items():
        print(f"{asset}: ${data['price']:,} at {data['fetched_at'].isoformat()}")