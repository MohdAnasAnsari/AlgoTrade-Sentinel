"""Read the watchlist from the DB when available, otherwise fall back to YAML."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


class WatchlistItem(TypedDict):
    ticker: str
    name: str
    sector: str


_REPO_ROOT = Path(__file__).parents[2]
_WATCHLIST_PATH = _REPO_ROOT / "config" / "watchlist.yaml"
_BACKEND_ENV_PATH = _REPO_ROOT / "backend" / ".env"

load_dotenv(_BACKEND_ENV_PATH)

_FALLBACK: list[WatchlistItem] = [
    {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
    {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
    {"ticker": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology"},
    {"ticker": "META", "name": "Meta Platforms Inc.", "sector": "Communication"},
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "sector": "ETF"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "sector": "ETF"},
    {"ticker": "GLD", "name": "SPDR Gold Shares", "sector": "Commodity ETF"},
]


def load_watchlist() -> list[WatchlistItem]:
    db_watchlist = _load_watchlist_from_db()
    if db_watchlist:
        return db_watchlist
    if _WATCHLIST_PATH.exists():
        with open(_WATCHLIST_PATH) as f:
            return yaml.safe_load(f)["tickers"]
    return _FALLBACK


def get_tickers() -> list[str]:
    return [item["ticker"] for item in load_watchlist()]


def _load_watchlist_from_db() -> list[WatchlistItem]:
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{(_REPO_ROOT / 'backend' / 'algotrade.db').as_posix()}")
    if database_url.startswith("sqlite:///./"):
        rel = database_url[len("sqlite:///./"):]
        database_url = f"sqlite:///{(_REPO_ROOT / 'backend' / rel).as_posix()}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        pool_pre_ping=True,
    )
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT ticker, company_name, sector
                    FROM watchlist
                    WHERE is_active = true
                    ORDER BY ticker
                    """
                )
            ).fetchall()
    except Exception:
        return []
    finally:
        engine.dispose()

    return [
        {
            "ticker": row[0],
            "name": row[1] or row[0],
            "sector": row[2] or "Unknown",
        }
        for row in rows
    ]
