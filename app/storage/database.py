"""
Database engine and session setup. Every module that reads or writes
Postgres imports SessionLocal (or Base, for defining models) from here -
this is the one place the connection is configured.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://crypto_pulse:crypto_pulse@localhost:5432/crypto_pulse",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
