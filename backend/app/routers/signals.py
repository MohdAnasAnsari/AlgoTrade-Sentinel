"""
Signals router — inference jobs + signal CRUD endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.signals import (
    InferenceJobStatus,
    LatestSignal,
    RunInferenceRequest,
    SignalHistoryPoint,
    SignalOut,
    StartInferenceResponse,
)
from app.services import signals_service

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.post("/run")
def run_inference(body: RunInferenceRequest) -> dict:
    """Kick off background batch inference. Returns job_id for polling."""
    job_id = signals_service.start_inference_job(body.model_dump())
    return ok(StartInferenceResponse(job_id=job_id, message="Inference job started"))


@router.get("/status/{job_id}")
def inference_status(job_id: str) -> dict:
    """Poll inference job status."""
    status = signals_service.get_job_status(job_id)
    if status is None:
        raise HTTPException(404, detail=f"Job {job_id} not found")
    return ok(InferenceJobStatus(job_id=job_id, **status))


@router.get("/latest")
def latest_signals(
    signal: Optional[str] = Query(None, description="Filter: BUY, SELL, HOLD"),
    db: Session = Depends(get_db),
) -> dict:
    """Return the most recent signal per ticker, optionally filtered."""
    rows = signals_service.get_latest_signals(db, signal_filter=signal)
    return ok([
        LatestSignal(
            ticker=r["ticker"],
            signal_date=r.get("signal_date"),
            signal=r.get("signal"),
            confidence=r.get("confidence"),
            prob_buy=r.get("prob_buy"),
            prob_sell=r.get("prob_sell"),
            prob_hold=r.get("prob_hold"),
            model_version=r.get("model_version"),
            explanation=r.get("explanation"),
        )
        for r in rows
    ])


@router.get("/history/{ticker}")
def ticker_signal_history(
    ticker: str,
    limit: int = Query(90, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """Return signal history for a ticker, newest first, joined with close price."""
    rows = signals_service.get_ticker_signal_history(ticker.upper(), db, limit=limit)
    return ok([
        SignalHistoryPoint(
            signal_date=r["signal_date"],
            signal=r["signal"],
            confidence=r.get("confidence"),
            close=r.get("close"),
        )
        for r in rows
    ])


@router.get("/ticker/{ticker}/latest")
def ticker_latest_signal(ticker: str, db: Session = Depends(get_db)) -> dict:
    """Return the most recent signal for a specific ticker."""
    row = signals_service.get_ticker_latest_signal(ticker.upper(), db)
    if not row:
        raise HTTPException(404, detail=f"No signals found for {ticker}")
    return ok(LatestSignal(**row))


@router.get("/{signal_id}")
def get_signal(signal_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single signal by id."""
    row = signals_service.get_signal_by_id(signal_id, db)
    if not row:
        raise HTTPException(404, detail=f"Signal {signal_id} not found")
    return ok(SignalOut(**row))
