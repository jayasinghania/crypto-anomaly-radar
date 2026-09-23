"""create initial tables

Revision ID: 0001
Revises:
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset", sa.String, nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ticks_asset", "ticks", ["asset"])
    op.create_index("ix_ticks_fetched_at", "ticks", ["fetched_at"])
    op.create_index("ix_ticks_asset_fetched_at", "ticks", ["asset", "fetched_at"])

    op.create_table(
        "bars",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset", sa.String, nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float, nullable=False),
        sa.Column("high", sa.Float, nullable=False),
        sa.Column("low", sa.Float, nullable=False),
        sa.Column("close", sa.Float, nullable=False),
    )
    op.create_index("ix_bars_asset", "bars", ["asset"])
    op.create_index("ix_bars_bucket_start", "bars", ["bucket_start"])
    op.create_index("ix_bars_asset_bucket", "bars", ["asset", "bucket_start"], unique=True)

    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset", sa.String, nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rolling_mean", sa.Float, nullable=True),
        sa.Column("rolling_std", sa.Float, nullable=True),
        sa.Column("z_score", sa.Float, nullable=True),
        sa.Column("is_anomaly", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_metrics_asset", "metrics", ["asset"])
    op.create_index("ix_metrics_bucket_start", "metrics", ["bucket_start"])

    op.create_table(
        "anomaly_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset", sa.String, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("z_score", sa.Float, nullable=False),
        sa.Column("price_at_event", sa.Float, nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_anomaly_events_asset", "anomaly_events", ["asset"])
    op.create_index("ix_anomaly_events_ts", "anomaly_events", ["ts"])


def downgrade() -> None:
    op.drop_table("anomaly_events")
    op.drop_table("metrics")
    op.drop_table("bars")
    op.drop_table("ticks")
