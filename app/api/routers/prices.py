from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import TickOut
from app.config import ASSETS
from app.storage.models import Tick

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/{asset}", response_model=list[TickOut])
def get_prices(
    asset: str,
    limit: int = Query(100, ge=1, le=1000, description="Max ticks to return, most recent first"),
    db: Session = Depends(get_db),
) -> list[Tick]:
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown asset '{asset}'. Tracked assets: {ASSETS}")

    return db.scalars(
        select(Tick)
        .where(Tick.asset == asset)
        .order_by(Tick.fetched_at.desc())
        .limit(limit)
    ).all()
