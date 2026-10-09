"""
Phase 6 - Forecast endpoints.

Both endpoints read the bars the analytics worker has already built, so
there is no new table and no migration. The math lives in
app/analytics/forecast.py; this file only loads data and shapes responses.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.aggregator import BAR_INTERVAL_SECONDS
from app.analytics.forecast import backtest, holt_forecast
from app.api.dependencies import get_db
from app.config import ASSETS
from app.storage.models import Bar

router = APIRouter(prefix="/forecast", tags=["forecast"])

MIN_BARS = 10


class ForecastPoint(BaseModel):
    bar_start: datetime
    price: float


class ForecastOut(BaseModel):
    asset: str
    horizon: int
    based_on_bars: int
    last_bar_start: datetime
    last_close: float
    forecast: list[ForecastPoint]


class AccuracyOut(BaseModel):
    asset: str
    horizon: int
    bars_used: int
    samples: int
    holt_mape: float | None
    naive_mape: float | None
    beats_naive: bool


def _load_bars(db: Session, asset: str, history: int) -> list[Bar]:
    """Most recent `history` bars for an asset, oldest first."""
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown asset '{asset}'. Tracked assets: {ASSETS}")

    bars = list(
        db.scalars(
            select(Bar)
            .where(Bar.asset == asset)
            .order_by(Bar.bucket_start.desc())
            .limit(history)
        ).all()
    )
    bars.reverse()

    if len(bars) < MIN_BARS:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough data yet: {len(bars)} bars for '{asset}', need at least {MIN_BARS}. "
                   f"Keep the ingestion scheduler and analytics worker running.",
        )
    return bars


@router.get("/{asset}", response_model=ForecastOut)
def get_forecast(
    asset: str,
    horizon: int = Query(5, ge=1, le=30, description="How many bars ahead to forecast"),
    history: int = Query(60, ge=MIN_BARS, le=1000, description="How many recent bars to learn from"),
    db: Session = Depends(get_db),
) -> ForecastOut:
    bars = _load_bars(db, asset, history)
    predictions = holt_forecast([b.close for b in bars], horizon)

    last = bars[-1]
    step = timedelta(seconds=BAR_INTERVAL_SECONDS)
    return ForecastOut(
        asset=asset,
        horizon=horizon,
        based_on_bars=len(bars),
        last_bar_start=last.bucket_start,
        last_close=last.close,
        forecast=[
            ForecastPoint(bar_start=last.bucket_start + step * (i + 1), price=p)
            for i, p in enumerate(predictions)
        ],
    )


@router.get("/{asset}/accuracy", response_model=AccuracyOut)
def get_accuracy(
    asset: str,
    horizon: int = Query(1, ge=1, le=30, description="Score the forecast this many bars ahead"),
    history: int = Query(200, ge=MIN_BARS, le=1000, description="How many recent bars to backtest over"),
    db: Session = Depends(get_db),
) -> AccuracyOut:
    """Walk-forward backtest: Holt vs the naive 'price stays the same' baseline."""
    bars = _load_bars(db, asset, history)
    result = backtest([b.close for b in bars], horizon=horizon)
    return AccuracyOut(asset=asset, bars_used=len(bars), **result)
