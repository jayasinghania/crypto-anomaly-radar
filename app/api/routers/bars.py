from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import BarOut
from app.config import ASSETS
from app.storage.models import Bar

router = APIRouter(prefix="/bars", tags=["bars"])


@router.get("/{asset}", response_model=list[BarOut])
def get_bars(
    asset: str,
    limit: int = Query(100, ge=1, le=1000, description="Max bars to return, most recent first"),
    db: Session = Depends(get_db),
) -> list[Bar]:
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown asset '{asset}'. Tracked assets: {ASSETS}")

    return db.scalars(
        select(Bar)
        .where(Bar.asset == asset)
        .order_by(Bar.bucket_start.desc())
        .limit(limit)
    ).all()
