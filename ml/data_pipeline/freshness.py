"""Data freshness checker.

Detects stale or missing data per ticker and returns a per-ticker report.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select

from ml.data_pipeline.database import SessionLocal, market_data_table
from ml.data_pipeline.watchlist import get_tickers


@dataclass
class FreshnessStatus:
    ticker: str
    last_date: date | None
    days_stale: int | None
    status: str  # 'fresh' | 'stale' | 'missing'


def _classify(last_date: date | None) -> tuple[int | None, str]:
    if last_date is None:
        return None, "missing"
    days = (date.today() - last_date).days
    # 4-day window accounts for weekends + public holidays
    return days, "fresh" if days <= 4 else "stale"


def check_freshness(tickers: list[str] | None = None) -> list[FreshnessStatus]:
    """Return freshness status for each ticker in the watchlist."""
    if tickers is None:
        tickers = get_tickers()

    with SessionLocal() as session:
        rows = session.execute(
            select(
                market_data_table.c.ticker,
                func.max(market_data_table.c.date).label("last_date"),
            )
            .where(market_data_table.c.ticker.in_(tickers))
            .group_by(market_data_table.c.ticker)
        ).fetchall()

    latest_map: dict[str, date] = {r.ticker: r.last_date for r in rows}

    report: list[FreshnessStatus] = []
    for ticker in tickers:
        last = latest_map.get(ticker)
        days, status = _classify(last)
        report.append(FreshnessStatus(ticker=ticker, last_date=last, days_stale=days, status=status))

    return report


def stale_tickers(tickers: list[str] | None = None) -> list[str]:
    """Return only tickers that are stale or missing."""
    return [r.ticker for r in check_freshness(tickers) if r.status != "fresh"]


if __name__ == "__main__":
    report = check_freshness()
    print(f"{'Ticker':<8} {'Status':<10} {'Last Date':<12} {'Days Stale'}")
    print("-" * 44)
    for r in report:
        print(
            f"{r.ticker:<8} {r.status:<10} "
            f"{str(r.last_date) if r.last_date else 'N/A':<12} "
            f"{r.days_stale if r.days_stale is not None else 'N/A'}"
        )
