from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.market import (
    IngestRequest,
)
from app.services.market_service import MarketService

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/tickers")
def get_tickers(db: Session = Depends(get_db)) -> dict:
    return ok(MarketService(db).get_tickers())


@router.get("/ohlcv/{ticker}")
def get_ohlcv(
    ticker: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> dict:
    rows = MarketService(db).get_ohlcv(ticker, start_date, end_date, limit)
    if not rows:
        raise HTTPException(404, f"No data found for {ticker.upper()}")
    return ok(rows)


@router.get("/latest/{ticker}")
def get_latest(ticker: str, db: Session = Depends(get_db)) -> dict:
    row = MarketService(db).get_latest(ticker)
    if not row:
        raise HTTPException(404, f"No data found for {ticker.upper()}")
    return ok(row)


@router.get("/stats/{ticker}")
def get_stats(ticker: str, db: Session = Depends(get_db)) -> dict:
    return ok(MarketService(db).get_stats(ticker))


@router.get("/freshness")
def get_freshness(db: Session = Depends(get_db)) -> dict:
    return ok(MarketService(db).get_freshness())


@router.post("/ingest")
def trigger_ingest(
    body: IngestRequest = IngestRequest(),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return ok(MarketService(db).ingest(body.tickers))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
