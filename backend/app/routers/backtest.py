"""Backtesting Center API router."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.backtest import (
    BacktestDetail,
    BacktestJobStatus,
    BacktestMetrics,
    BacktestSummary,
    DrawdownPoint,
    EquityPoint,
    StartBacktestRequest,
    StartBacktestResponse,
    Trade,
)
from app.services import backtest_service as svc

router = APIRouter(tags=["backtest"])


# ---------------------------------------------------------------------------
# Trigger & status
# ---------------------------------------------------------------------------

@router.post("/api/backtest/run")
def run_backtest(body: StartBacktestRequest) -> dict:
    """Trigger a background backtest job."""
    job_id = svc.start_backtest_job(body.model_dump())
    return ok(StartBacktestResponse(job_id=job_id, message=f"Backtest started for {len(body.tickers)} ticker(s)"))


@router.get("/api/backtest/status/{job_id}")
def backtest_status(job_id: str) -> dict:
    """Poll job status."""
    job = svc.get_job_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return ok(BacktestJobStatus(job_id=job_id, **job))


# ---------------------------------------------------------------------------
# Query endpoints — specific paths BEFORE /{run_id}
# ---------------------------------------------------------------------------

@router.get("/api/backtest/runs")
def list_runs(limit: int = Query(200, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    """Return all backtest run summaries."""
    rows = svc.list_backtest_runs(db, limit=limit)
    return ok([_to_summary(r) for r in rows])


@router.get("/api/backtest/compare")
def compare_runs(run_ids: str = Query(..., description="Comma-separated run_ids"), db: Session = Depends(get_db)) -> dict:
    """Compare multiple runs side by side."""
    ids = [r.strip() for r in run_ids.split(",") if r.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Provide at least one run_id")
    rows = svc.compare_runs(ids, db)
    return ok([_to_summary(r) for r in rows])


@router.get("/api/backtest/{run_id}/equity")
def get_equity(run_id: str, db: Session = Depends(get_db)) -> dict:
    row = svc.get_backtest_detail(run_id, db)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    data = json.loads(row.get("equity_curve_json") or "[]")
    return ok([EquityPoint(**e) for e in data])


@router.get("/api/backtest/{run_id}/drawdown")
def get_drawdown(run_id: str, db: Session = Depends(get_db)) -> dict:
    row = svc.get_backtest_detail(run_id, db)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    data = json.loads(row.get("drawdown_json") or "[]")
    return ok([DrawdownPoint(**d) for d in data])


@router.get("/api/backtest/{run_id}/trades")
def get_trades(run_id: str, db: Session = Depends(get_db)) -> dict:
    row = svc.get_backtest_detail(run_id, db)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    data = json.loads(row.get("trades_json") or "[]")
    return ok([Trade(**t) for t in data])


@router.get("/api/backtest/{run_id}/metrics")
def get_metrics(run_id: str, db: Session = Depends(get_db)) -> dict:
    row = svc.get_backtest_detail(run_id, db)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return ok(BacktestMetrics(
        run_id=row["run_id"], ticker=row["ticker"],
        total_return=_f(row, "total_return"),
        annualized_return=_f(row, "annualized_return"),
        benchmark_return=_f(row, "benchmark_return"),
        alpha=_f(row, "alpha"),
        max_drawdown=_f(row, "max_drawdown"),
        sharpe_ratio=_f(row, "sharpe_ratio"),
        sortino_ratio=_f(row, "sortino_ratio"),
        calmar_ratio=_f(row, "calmar_ratio"),
        daily_volatility=_f(row, "daily_volatility"),
        total_trades=row.get("total_trades"),
        win_rate=_f(row, "win_rate"),
        avg_win=_f(row, "avg_win"),
        avg_loss=_f(row, "avg_loss"),
        profit_factor=_f(row, "profit_factor"),
        avg_holding_days=_f(row, "avg_holding_days"),
    ))


@router.get("/api/backtest/{run_id}")
def get_detail(run_id: str, db: Session = Depends(get_db)) -> dict:
    """Return full backtest detail including equity curve, drawdown, and trades."""
    row = svc.get_backtest_detail(run_id, db)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    equity  = [EquityPoint(**e) for e in json.loads(row.get("equity_curve_json") or "[]")]
    dd      = [DrawdownPoint(**d) for d in json.loads(row.get("drawdown_json") or "[]")]
    trades  = [Trade(**t) for t in json.loads(row.get("trades_json") or "[]")]
    monthly = json.loads(row.get("monthly_returns_json") or "{}")

    return ok(BacktestDetail(
        **_to_summary(row).model_dump(),
        transaction_cost  = _f(row, "transaction_cost"),
        slippage          = _f(row, "slippage"),
        position_frac     = _f(row, "position_frac"),
        equity_curve      = equity,
        drawdown          = dd,
        trades            = trades,
        monthly_returns   = monthly,
    ))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _f(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    return float(v) if v is not None else None


def _to_summary(row: dict) -> BacktestSummary:
    return BacktestSummary(
        run_id           = row["run_id"],
        batch_id         = row.get("batch_id"),
        ticker           = row["ticker"],
        strategy_name    = row.get("strategy_name"),
        model_run_id     = row.get("model_run_id"),
        start_date       = str(row["start_date"])  if row.get("start_date")  else None,
        end_date         = str(row["end_date"])    if row.get("end_date")    else None,
        initial_capital  = _f(row, "initial_capital"),
        total_return     = _f(row, "total_return"),
        annualized_return= _f(row, "annualized_return"),
        benchmark_return = _f(row, "benchmark_return"),
        alpha            = _f(row, "alpha"),
        max_drawdown     = _f(row, "max_drawdown"),
        sharpe_ratio     = _f(row, "sharpe_ratio"),
        sortino_ratio    = _f(row, "sortino_ratio"),
        calmar_ratio     = _f(row, "calmar_ratio"),
        daily_volatility = _f(row, "daily_volatility"),
        total_trades     = row.get("total_trades"),
        win_rate         = _f(row, "win_rate"),
        avg_win          = _f(row, "avg_win"),
        avg_loss         = _f(row, "avg_loss"),
        profit_factor    = _f(row, "profit_factor"),
        avg_holding_days = _f(row, "avg_holding_days"),
        created_at       = str(row["created_at"]) if row.get("created_at") else None,
    )
