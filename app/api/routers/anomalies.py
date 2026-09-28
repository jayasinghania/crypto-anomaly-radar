from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import AnomalyEventOut
from app.config import ASSETS
from app.storage.models import AnomalyEvent

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyEventOut])
def list_anomalies(
    asset: str | None = Query(None, description="Filter to one asset; omit for all tracked assets"),
    limit: int = Query(50, ge=1, le=500, description="Max events to return, most recent first"),
    db: Session = Depends(get_db),
) -> list[AnomalyEvent]:
    if asset is not None and asset not in ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown asset '{asset}'. Tracked assets: {ASSETS}")

    stmt = select(AnomalyEvent).order_by(AnomalyEvent.ts.desc()).limit(limit)
    if asset:
        stmt = stmt.where(AnomalyEvent.asset == asset)

    return db.scalars(stmt).all()
