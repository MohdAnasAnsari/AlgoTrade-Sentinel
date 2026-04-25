"""Market data ingestion pipeline.

Downloads OHLCV data from yfinance and upserts into the market_data table.

Usage (from repo root):
    python -m ml.data_pipeline.ingest
    python -m ml.data_pipeline.ingest --tickers AAPL MSFT
    python -m ml.data_pipeline.ingest --period 1y
"""
from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass
from datetime import date

import pandas as pd
import yfinance as yf
from sqlalchemy import select

from ml.data_pipeline.database import SessionLocal, create_tables, market_data_table
from ml.data_pipeline.watchlist import get_tickers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
RATE_LIMIT_DELAY = 0.5  # seconds between tickers


@dataclass
class IngestResult:
    ticker: str
    rows_added: int
    success: bool
    error: str | None = None


def download_ticker(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Download OHLCV data with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download(
                ticker,
                period=period,
                auto_adjust=False,
                progress=False,
                actions=False,
            )
            if df.empty:
                logger.warning("%s attempt %d: empty dataframe", ticker, attempt)
                time.sleep(RETRY_DELAY)
                continue

            # Flatten MultiIndex (yfinance >=0.2.x behaviour for single ticker)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            return df.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            )
        except Exception as exc:
            logger.warning("%s attempt %d failed: %s", ticker, attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    return pd.DataFrame()


def _safe_float(val) -> float | None:
    try:
        v = float(val)
        return None if (v != v) else v
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def ingest_ticker(ticker: str, period: str = "5y") -> IngestResult:
    """Download and store data for a single ticker."""
    df = download_ticker(ticker, period)
    if df.empty:
        return IngestResult(ticker=ticker, rows_added=0, success=False, error="No data returned")

    with SessionLocal() as session:
        # Fetch existing dates for this ticker
        existing = {
            row[0]
            for row in session.execute(
                select(market_data_table.c.date).where(
                    market_data_table.c.ticker == ticker
                )
            )
        }

        rows_to_insert = []
        for ts, row in df.iterrows():
            row_date: date = ts.date() if hasattr(ts, "date") else ts
            if row_date in existing:
                continue
            rows_to_insert.append(
                {
                    "ticker": ticker,
                    "date": row_date,
                    "open": _safe_float(row.get("open")),
                    "high": _safe_float(row.get("high")),
                    "low": _safe_float(row.get("low")),
                    "close": _safe_float(row.get("close")),
                    "adj_close": _safe_float(row.get("adj_close")),
                    "volume": _safe_int(row.get("volume")),
                }
            )

        if rows_to_insert:
            session.execute(market_data_table.insert(), rows_to_insert)
            session.commit()

    return IngestResult(ticker=ticker, rows_added=len(rows_to_insert), success=True)


def run_ingest(tickers: list[str] | None = None, period: str = "5y") -> list[IngestResult]:
    """Ingest data for a list of tickers (default: full watchlist)."""
    create_tables()

    if tickers is None:
        tickers = get_tickers()

    logger.info("Starting ingestion for %d tickers: %s", len(tickers), tickers)
    results: list[IngestResult] = []

    for i, ticker in enumerate(tickers, 1):
        logger.info("[%d/%d] Processing %s …", i, len(tickers), ticker)
        result = ingest_ticker(ticker, period)
        results.append(result)

        if result.success:
            logger.info("  ✓ %s — +%d rows", ticker, result.rows_added)
        else:
            logger.error("  ✗ %s — %s", ticker, result.error)

        time.sleep(RATE_LIMIT_DELAY)

    successes = sum(1 for r in results if r.success)
    total_rows = sum(r.rows_added for r in results)
    logger.info(
        "Ingestion complete: %d/%d succeeded, %d new rows total",
        successes,
        len(tickers),
        total_rows,
    )
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest market data")
    parser.add_argument("--tickers", nargs="+", help="Tickers to ingest (default: watchlist)")
    parser.add_argument("--period", default="5y", help="yfinance period string (default: 5y)")
    args = parser.parse_args()
    run_ingest(tickers=args.tickers, period=args.period)
