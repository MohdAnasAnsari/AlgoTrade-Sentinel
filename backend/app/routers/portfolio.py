from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.portfolio import (
    OrderOut,
    OrdersResponse,
    PnLBreakdown,
    PortfolioHistoryPoint,
    PortfolioSummary,
    PositionDetail,
    PositionOut,
)
from app.services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary")
def portfolio_summary(db: Session = Depends(get_db)) -> dict:
    return ok(PortfolioSummary(**portfolio_service.get_summary(db)))


@router.get("/positions")
def portfolio_positions(db: Session = Depends(get_db)) -> dict:
    return ok([PositionOut.model_validate(row) for row in portfolio_service.get_open_positions(db)])


@router.get("/positions/{ticker}")
def portfolio_position_detail(ticker: str, db: Session = Depends(get_db)) -> dict:
    detail = portfolio_service.get_position_detail(db, ticker)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No position found for {ticker.upper()}")
    return ok(PositionDetail(
        position=PositionOut.model_validate(detail["position"]),
        orders=[OrderOut.model_validate(row) for row in detail["orders"]],
    ))


@router.get("/orders")
def portfolio_orders(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_type: str | None = Query(None),
    ticker: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    payload = portfolio_service.get_orders(
        db,
        limit=limit,
        offset=offset,
        order_type=order_type,
        ticker=ticker,
    )
    return ok(OrdersResponse(
        total=payload["total"],
        items=[OrderOut.model_validate(row) for row in payload["items"]],
    ))


@router.get("/history")
def portfolio_history(days: int | None = Query(None, ge=1, le=3650), db: Session = Depends(get_db)) -> dict:
    return ok([PortfolioHistoryPoint(**row) for row in portfolio_service.get_history(db, days=days)])


@router.get("/pnl")
def portfolio_pnl(db: Session = Depends(get_db)) -> dict:
    return ok(PnLBreakdown(**portfolio_service.get_pnl_breakdown(db)))
