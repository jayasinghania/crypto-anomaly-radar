"""
ORM models for the storage layer.

Four tables, matching the original blueprint:
- Tick: raw price readings, exactly as ingested (append-only, Phase 1 -> here)
- Bar: OHLCV aggregated per asset per time bucket (populated in Phase 3)
- Metric: rolling stats + anomaly flag per bar (populated in Phase 3)
- AnomalyEvent: a queryable log of every anomaly ever flagged (Phase 3)

Bar/Metric/AnomalyEvent are defined now so the schema is complete and
migratable in one shot, even though nothing writes to them until Phase 3.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String

from app.storage.database import Base


class Tick(Base):
    __tablename__ = "ticks"

    id = Column(Integer, primary_key=True)
    asset = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_ticks_asset", "asset"),
        Index("ix_ticks_fetched_at", "fetched_at"),
        Index("ix_ticks_asset_fetched_at", "asset", "fetched_at"),
    )


class Bar(Base):
    __tablename__ = "bars"

    id = Column(Integer, primary_key=True)
    asset = Column(String, nullable=False)
    bucket_start = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_bars_asset", "asset"),
        Index("ix_bars_bucket_start", "bucket_start"),
        Index("ix_bars_asset_bucket", "asset", "bucket_start", unique=True),
    )


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    asset = Column(String, nullable=False)
    bucket_start = Column(DateTime(timezone=True), nullable=False)
    rolling_mean = Column(Float, nullable=True)
    rolling_std = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_metrics_asset", "asset"),
        Index("ix_metrics_bucket_start", "bucket_start"),
    )


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True)
    asset = Column(String, nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False)
    z_score = Column(Float, nullable=False)
    price_at_event = Column(Float, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_anomaly_events_asset", "asset"),
        Index("ix_anomaly_events_ts", "ts"),
    )
