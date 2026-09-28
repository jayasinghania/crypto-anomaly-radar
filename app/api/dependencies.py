"""
FastAPI dependency that yields one DB session per request and always
closes it afterward. This is a different pattern from the repository
functions used in ingestion/analytics (which open and close their own
session per call) - here, the session's lifetime is tied to the HTTP
request, which is the standard FastAPI + SQLAlchemy pattern.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.storage.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
