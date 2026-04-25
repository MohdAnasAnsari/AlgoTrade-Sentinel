from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.watchlist import AddWatchlistRequest, WatchlistItemOut, WatchlistMutationResponse
from app.services import watchlist_service

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("/")
def get_watchlist(db: Session = Depends(get_db)) -> dict:
    return ok([WatchlistItemOut.model_validate(row) for row in watchlist_service.list_watchlist(db)])


@router.post("/add")
def add_watchlist(body: AddWatchlistRequest, db: Session = Depends(get_db)) -> dict:
    return ok(WatchlistMutationResponse(
        **watchlist_service.add_watchlist_ticker(
            db,
            ticker=body.ticker,
            company_name=body.company_name,
            sector=body.sector,
        )
    ))


@router.delete("/{ticker}")
def remove_watchlist(ticker: str, db: Session = Depends(get_db)) -> dict:
    return ok(WatchlistMutationResponse(**watchlist_service.remove_watchlist_ticker(db, ticker)))
