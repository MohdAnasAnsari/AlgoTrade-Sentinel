from __future__ import annotations

from datetime import date
import threading
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.features import LabelsData
from app.models.market import MarketData
from app.models.portfolio import Order, PortfolioSnapshot, Position
from app.models.signals import Signal
from app.services.settings_service import get_portfolio_config
from app.services.watchlist_service import ensure_watchlist_seeded, get_watchlist_map
from ml.portfolio.paper_trader import PortfolioConfig, simulate_paper_portfolio

_PORTFOLIO_STATE_LOCK = threading.Lock()


def ensure_portfolio_state(db: Session) -> None:
    ensure_watchlist_seeded(db)
    if not _portfolio_state_needs_rebuild(db):
        return

    with _PORTFOLIO_STATE_LOCK:
        db.expire_all()
        if not _portfolio_state_needs_rebuild(db):
            return
        rebuild_portfolio_state(db)


def rebuild_portfolio_state(db: Session) -> None:
    config = get_portfolio_config(db)
    market_rows = _load_market_rows(db)
    watchlist_map = get_watchlist_map(db)
    signal_rows = _load_signal_rows(db)

    simulated = simulate_paper_portfolio(
        market_rows=market_rows,
        signal_rows=signal_rows,
        watchlist=watchlist_map,
        config=PortfolioConfig(
            initial_cash=float(config["initial_cash"]),
            max_positions=int(config["max_positions"]),
            transaction_cost=float(config["transaction_cost"]),
        ),
    )

    db.query(Order).delete(synchronize_session=False)
    db.query(Position).delete(synchronize_session=False)
    db.query(PortfolioSnapshot).delete(synchronize_session=False)

    for row in simulated["positions"]:
        db.add(
            Position(
                ticker=row["ticker"],
                entry_date=row["entry_date"],
                entry_price=float(row["entry_price"]),
                shares=float(row["shares"]),
                current_price=_maybe_float(row.get("current_price")),
                market_value=float(row["market_value"]),
                unrealized_pnl=float(row["unrealized_pnl"]),
                unrealized_pnl_pct=float(row["unrealized_pnl_pct"]),
                status=row["status"],
                company_name=row.get("company_name"),
                sector=row.get("sector"),
            )
        )

    for row in simulated["orders"]:
        db.add(
            Order(
                ticker=row["ticker"],
                order_date=row["order_date"],
                order_type=row["order_type"],
                price=float(row["price"]),
                shares=float(row["shares"]),
                total_value=float(row["total_value"]),
                transaction_cost=float(row["transaction_cost"]),
                signal_id=row.get("signal_id"),
            )
        )

    for row in simulated["snapshots"]:
        db.add(
            PortfolioSnapshot(
                snapshot_date=row["snapshot_date"],
                total_value=float(row["total_value"]),
                cash_balance=float(row["cash_balance"]),
                invested_value=float(row["invested_value"]),
                total_pnl=float(row["total_pnl"]),
                total_pnl_pct=float(row["total_pnl_pct"]),
                realized_pnl=float(row["realized_pnl"]),
                unrealized_pnl=float(row["unrealized_pnl"]),
            )
        )

    if not simulated["snapshots"] and market_rows:
        start_date = min(row["date"] for row in market_rows)
        db.add(
            PortfolioSnapshot(
                snapshot_date=start_date,
                total_value=float(config["initial_cash"]),
                cash_balance=float(config["initial_cash"]),
                invested_value=0.0,
                total_pnl=0.0,
                total_pnl_pct=0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
            )
        )

    db.commit()


def get_summary(db: Session) -> dict[str, Any]:
    ensure_portfolio_state(db)
    config = get_portfolio_config(db)
    latest = db.query(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_date.desc()).first()
    previous = (
        db.query(PortfolioSnapshot)
        .order_by(PortfolioSnapshot.snapshot_date.desc())
        .offset(1)
        .first()
    )
    open_positions = get_open_positions(db)
    daily_change = 0.0
    daily_change_pct = 0.0
    if latest and previous:
        daily_change = float(latest.total_value) - float(previous.total_value)
        daily_change_pct = (daily_change / float(previous.total_value) * 100.0) if float(previous.total_value) else 0.0

    return {
        "snapshot_date": latest.snapshot_date if latest else None,
        "total_value": _snapshot_value(latest, "total_value", float(config["initial_cash"])),
        "daily_change": daily_change,
        "daily_change_pct": daily_change_pct,
        "total_pnl": _snapshot_value(latest, "total_pnl", 0.0),
        "total_pnl_pct": _snapshot_value(latest, "total_pnl_pct", 0.0),
        "realized_pnl": _snapshot_value(latest, "realized_pnl", 0.0),
        "unrealized_pnl": _snapshot_value(latest, "unrealized_pnl", 0.0),
        "cash_balance": _snapshot_value(latest, "cash_balance", float(config["initial_cash"])),
        "invested_value": _snapshot_value(latest, "invested_value", 0.0),
        "open_positions": len(open_positions),
        "initial_capital": float(config["initial_cash"]),
        "best_position": _highlight(open_positions, best=True),
        "worst_position": _highlight(open_positions, best=False),
    }


def get_open_positions(db: Session) -> list[Position]:
    ensure_portfolio_state(db)
    return (
        db.query(Position)
        .filter(Position.status == "OPEN")
        .order_by(Position.unrealized_pnl_pct.desc(), Position.ticker.asc())
        .all()
    )


def get_position_detail(db: Session, ticker: str) -> dict[str, Any] | None:
    ensure_portfolio_state(db)
    position = (
        db.query(Position)
        .filter(Position.ticker == ticker.upper(), Position.status == "OPEN")
        .order_by(Position.entry_date.desc())
        .first()
    )
    if position is None:
        position = (
            db.query(Position)
            .filter(Position.ticker == ticker.upper())
            .order_by(Position.entry_date.desc())
            .first()
        )
    if position is None:
        return None
    orders = (
        db.query(Order)
        .filter(Order.ticker == ticker.upper())
        .order_by(Order.order_date.desc(), Order.created_at.desc())
        .all()
    )
    return {"position": position, "orders": orders}


def get_orders(
    db: Session,
    *,
    limit: int = 25,
    offset: int = 0,
    order_type: str | None = None,
    ticker: str | None = None,
) -> dict[str, Any]:
    ensure_portfolio_state(db)
    query = db.query(Order)
    if order_type:
        query = query.filter(Order.order_type == order_type.upper())
    if ticker:
        query = query.filter(Order.ticker == ticker.upper())
    total = query.count()
    items = (
        query.order_by(Order.order_date.desc(), Order.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": items}


def get_history(db: Session, days: int | None = None) -> list[dict[str, Any]]:
    ensure_portfolio_state(db)
    query = db.query(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_date.asc())
    rows = query.all()
    if days is not None and days > 0:
        rows = rows[-days:]
    return [
        {
            "snapshot_date": row.snapshot_date,
            "total_value": float(row.total_value),
            "cash_balance": float(row.cash_balance),
            "invested_value": float(row.invested_value),
            "total_pnl": float(row.total_pnl),
            "total_pnl_pct": float(row.total_pnl_pct),
            "realized_pnl": float(row.realized_pnl),
            "unrealized_pnl": float(row.unrealized_pnl),
        }
        for row in rows
    ]


def get_pnl_breakdown(db: Session) -> dict[str, Any]:
    summary = get_summary(db)
    open_positions = get_open_positions(db)
    return {
        "realized_pnl": summary["realized_pnl"],
        "unrealized_pnl": summary["unrealized_pnl"],
        "total_pnl": summary["total_pnl"],
        "total_pnl_pct": summary["total_pnl_pct"],
        "best_position": _highlight(open_positions, best=True),
        "worst_position": _highlight(open_positions, best=False),
    }


def latest_orders_for_alerts(db: Session, limit: int = 10) -> list[Order]:
    ensure_portfolio_state(db)
    return (
        db.query(Order)
        .order_by(Order.order_date.desc(), Order.created_at.desc())
        .limit(limit)
        .all()
    )


def _load_market_rows(db: Session) -> list[dict[str, Any]]:
    rows = db.query(MarketData).order_by(MarketData.date.asc(), MarketData.ticker.asc()).all()
    return [
        {
            "ticker": row.ticker,
            "date": row.date,
            "open": float(row.open),
            "close": float(row.close),
        }
        for row in rows
        if row.open is not None and row.close is not None
    ]


def _load_signal_rows(db: Session) -> list[dict[str, Any]]:
    signals = db.query(Signal).order_by(Signal.signal_date.asc(), Signal.ticker.asc()).all()
    if signals:
        return [
            {
                "ticker": row.ticker,
                "signal_date": row.signal_date,
                "signal": row.signal,
                "signal_id": row.id,
            }
            for row in signals
            if row.signal in {"BUY", "SELL"}
        ]
    label_rows = (
        db.query(LabelsData)
        .filter(LabelsData.signal_label.isnot(None))
        .order_by(LabelsData.date.asc(), LabelsData.ticker.asc())
        .all()
    )
    return [
        {
            "ticker": row.ticker,
            "signal_date": row.date,
            "signal": row.signal_label,
            "signal_id": None,
        }
        for row in label_rows
        if row.signal_label in {"BUY", "SELL"}
    ]


def _snapshot_value(snapshot: PortfolioSnapshot | None, field: str, default: float) -> float:
    if snapshot is None:
        return default
    return float(getattr(snapshot, field))


def _maybe_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _highlight(positions: list[Position], *, best: bool) -> dict[str, Any] | None:
    if not positions:
        return None
    chosen = max(positions, key=lambda row: float(row.unrealized_pnl_pct)) if best else min(
        positions, key=lambda row: float(row.unrealized_pnl_pct)
    )
    return {
        "ticker": chosen.ticker,
        "company_name": chosen.company_name,
        "market_value": float(chosen.market_value),
        "unrealized_pnl": float(chosen.unrealized_pnl),
        "unrealized_pnl_pct": float(chosen.unrealized_pnl_pct),
    }


def _portfolio_state_needs_rebuild(db: Session) -> bool:
    latest_market_date = db.query(func.max(MarketData.date)).scalar()
    if latest_market_date is None:
        return False

    latest_snapshot_date = db.query(func.max(PortfolioSnapshot.snapshot_date)).scalar()
    if latest_snapshot_date != latest_market_date:
        return True

    return db.query(PortfolioSnapshot.id).limit(1).first() is None
