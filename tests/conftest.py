"""
Shared test setup.

Tests never touch your real Postgres. They use a throwaway in-memory
SQLite database built from the same SQLAlchemy models, so they run
anywhere (your laptop, CI) with no Docker and no services.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.storage import models  # noqa: F401  (registers the tables on Base)
from app.storage.database import Base


@pytest.fixture
def db_session_factory():
    """A fresh, empty in-memory database for every single test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection, so every session sees the same data
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()
