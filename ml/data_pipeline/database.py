"""Standalone database connection for ML pipeline scripts.

Reads DATABASE_URL from environment/.env — same database as the backend.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import sessionmaker

# Load .env from repo root or backend/
for env_path in [
    Path(__file__).parents[2] / ".env",
    Path(__file__).parents[2] / "backend" / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path)
        break

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./algotrade.db")

# Resolve relative SQLite paths to absolute (scripts may run from any cwd)
if DATABASE_URL.startswith("sqlite:///./"):
    rel = DATABASE_URL[len("sqlite:///./"):]
    abs_path = Path(__file__).parents[2] / "backend" / rel
    DATABASE_URL = f"sqlite:///{abs_path.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Table definition (mirrors backend/app/models/market.py)
# ---------------------------------------------------------------------------
metadata = MetaData()

market_data_table = Table(
    "market_data",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticker", String(20), nullable=False),
    Column("date", Date, nullable=False),
    Column("open", Numeric(16, 6)),
    Column("high", Numeric(16, 6)),
    Column("low", Numeric(16, 6)),
    Column("close", Numeric(16, 6)),
    Column("adj_close", Numeric(16, 6)),
    Column("volume", BigInteger),
    Column("created_at", DateTime, server_default=text("CURRENT_TIMESTAMP")),
    UniqueConstraint("ticker", "date", name="uq_market_data_ticker_date"),
    Index("ix_market_data_ticker", "ticker"),
    Index("ix_market_data_date", "date"),
)


def create_tables() -> None:
    """Create tables if they do not exist (idempotent)."""
    metadata.create_all(engine)
