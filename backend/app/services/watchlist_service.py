from __future__ import annotations

import logging
import threading
from typing import Any

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.portfolio import Watchlist
from ml.data_pipeline.watchlist import load_watchlist

logger = logging.getLogger(__name__)
_WATCHLIST_SEED_LOCK = threading.Lock()


def ensure_watchlist_seeded(db: Session) -> None:
    if _watchlist_has_rows(db):
        return

    with _WATCHLIST_SEED_LOCK:
        db.expire_all()
        if _watchlist_has_rows(db):
            return

        defaults = load_watchlist()
        for item in defaults:
            db.add(
                Watchlist(
                    ticker=item["ticker"].upper(),
                    company_name=item.get("name") or item["ticker"].upper(),
                    sector=item.get("sector"),
                    is_active=True,
                )
            )
        db.commit()


def list_watchlist(db: Session) -> list[Watchlist]:
    ensure_watchlist_seeded(db)
    return db.query(Watchlist).order_by(Watchlist.ticker.asc()).all()


def get_watchlist_map(db: Session) -> dict[str, dict[str, str | None]]:
    ensure_watchlist_seeded(db)
    rows = db.query(Watchlist).filter(Watchlist.is_active.is_(True)).all()
    return {
        row.ticker: {
            "company_name": row.company_name,
            "name": row.company_name,
            "sector": row.sector,
        }
        for row in rows
    }


def add_watchlist_ticker(db: Session, ticker: str, company_name: str | None, sector: str | None) -> dict[str, Any]:
    ensure_watchlist_seeded(db)
    normalized = ticker.upper().strip()
    row = db.query(Watchlist).filter(Watchlist.ticker == normalized).first()
    if row is None:
        row = Watchlist(
            ticker=normalized,
            company_name=company_name or normalized,
            sector=sector,
            is_active=True,
        )
        db.add(row)
    else:
        row.company_name = company_name or row.company_name or normalized
        row.sector = sector or row.sector
        row.is_active = True
    db.commit()

    threading.Thread(target=_run_watchlist_pipeline, args=(normalized,), daemon=True).start()
    return {
        "success": True,
        "ticker": normalized,
        "pipeline_status": "queued",
        "message": f"{normalized} was added to the watchlist and pipeline tasks were queued.",
    }


def remove_watchlist_ticker(db: Session, ticker: str) -> dict[str, Any]:
    ensure_watchlist_seeded(db)
    normalized = ticker.upper().strip()
    row = db.query(Watchlist).filter(Watchlist.ticker == normalized).first()
    if row is None:
        return {
            "success": False,
            "ticker": normalized,
            "pipeline_status": None,
            "message": f"{normalized} is not in the watchlist.",
        }
    row.is_active = False
    db.commit()
    return {
        "success": True,
        "ticker": normalized,
        "pipeline_status": None,
        "message": f"{normalized} was removed from the active watchlist.",
    }


def _run_watchlist_pipeline(ticker: str) -> None:
    db = SessionLocal()
    try:
        from app.services.feature_service import FeatureService
        from app.services.market_service import MarketService
        from app.services.signals_service import start_inference_job

        try:
            MarketService(db).ingest([ticker])
        except Exception as exc:
            logger.info("Watchlist ingest skipped for %s: %s", ticker, exc)

        try:
            FeatureService(db).run_pipeline(tickers=[ticker], build_ds=False)
        except Exception as exc:
            logger.info("Watchlist feature build skipped for %s: %s", ticker, exc)

        try:
            start_inference_job({"tickers": [ticker]})
        except Exception as exc:
            logger.info("Watchlist inference skipped for %s: %s", ticker, exc)
    finally:
        db.close()


def _watchlist_has_rows(db: Session) -> bool:
    return db.query(Watchlist.id).limit(1).first() is not None
