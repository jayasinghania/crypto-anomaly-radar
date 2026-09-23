"""
Thin data-access layer. Ingestion and analytics code call functions like
save_tick() rather than opening SQLAlchemy sessions themselves - keeps
the DB details in one place, and makes this layer easy to swap or mock
in tests later.
"""

from datetime import datetime

from app.storage.database import SessionLocal
from app.storage.models import Tick


def save_tick(asset: str, price: float, fetched_at: datetime) -> None:
    """Persist one price reading. Opens and closes its own session."""
    with SessionLocal() as session:
        session.add(Tick(asset=asset, price=price, fetched_at=fetched_at))
        session.commit()
