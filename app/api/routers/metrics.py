from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import MetricOut
from app.config import ASSETS
from app.storage.models import Metric

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/{asset}", response_model=list[MetricOut])
def get_metrics(
    asset: str,
    limit: int = Query(100, ge=1, le=1000, description="Max metric rows to return, most recent first"),
    db: Session = Depends(get_db),
) -> list[Metric]:
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown asset '{asset}'. Tracked assets: {ASSETS}")

    return db.scalars(
        select(Metric)
        .where(Metric.asset == asset)
        .order_by(Metric.bucket_start.desc())
        .limit(limit)
    ).all()
