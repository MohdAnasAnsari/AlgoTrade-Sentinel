"""Prefect flow: daily market data ingestion.

Schedule: Mon–Fri at 16:30 ET (21:30 UTC / 20:30 UTC during EDT).

Deploy:
    prefect deploy mlops/flows/ingest_flow.py:market_data_ingest_flow \\
        --name "daily-market-ingest" \\
        --cron "30 21 * * 1-5"

Or run once immediately:
    python mlops/flows/ingest_flow.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make repo packages importable when running directly
sys.path.insert(0, str(Path(__file__).parents[2]))

from prefect import flow, get_run_logger, task
from prefect.schedules import CronSchedule

from ml.data_pipeline.freshness import check_freshness
from ml.data_pipeline.ingest import IngestResult, ingest_ticker
from ml.data_pipeline.watchlist import get_tickers


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@task(retries=2, retry_delay_seconds=30, name="ingest-ticker")
def ingest_ticker_task(ticker: str, period: str = "5y") -> IngestResult:
    logger = get_run_logger()
    result = ingest_ticker(ticker, period)
    if result.success:
        logger.info("%s: +%d rows", ticker, result.rows_added)
    else:
        logger.error("%s: FAILED — %s", ticker, result.error)
    return result


@task(name="check-freshness")
def freshness_task(tickers: list[str]) -> dict[str, str]:
    statuses = check_freshness(tickers)
    return {s.ticker: s.status for s in statuses}


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


@flow(
    name="market-data-ingest",
    description="Daily OHLCV ingestion for all watchlist tickers via yfinance",
)
def market_data_ingest_flow(
    tickers: list[str] | None = None,
    period: str = "5y",
    only_stale: bool = False,
) -> dict:
    logger = get_run_logger()

    if tickers is None:
        tickers = get_tickers()

    if only_stale:
        stale = [s.ticker for s in check_freshness(tickers) if s.status != "fresh"]
        logger.info("Stale/missing tickers: %s", stale)
        tickers = stale if stale else tickers

    logger.info("Ingesting %d tickers: %s", len(tickers), tickers)

    results: list[IngestResult] = [ingest_ticker_task.submit(t, period) for t in tickers]
    results = [r.result() for r in results]

    freshness = freshness_task(tickers)

    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    total_rows = sum(r.rows_added for r in successes)

    logger.info(
        "Done: %d succeeded / %d failed / %d new rows",
        len(successes),
        len(failures),
        total_rows,
    )

    return {
        "tickers_succeeded": [r.ticker for r in successes],
        "tickers_failed": [r.ticker for r in failures],
        "rows_added": total_rows,
        "freshness": freshness,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    market_data_ingest_flow()
