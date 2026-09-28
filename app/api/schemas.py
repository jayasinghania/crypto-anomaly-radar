"""
Pydantic response models. These define the API's actual public contract
- what a client can rely on - independent of the SQLAlchemy models, so
internal storage changes don't automatically become API-breaking changes.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset: str
    price: float
    fetched_at: datetime


class BarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset: str
    bucket_start: datetime
    open: float
    high: float
    low: float
    close: float


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset: str
    bucket_start: datetime
    rolling_mean: float | None
    rolling_std: float | None
    z_score: float | None
    is_anomaly: bool


class AnomalyEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset: str
    ts: datetime
    z_score: float
    price_at_event: float
    resolved_at: datetime | None
