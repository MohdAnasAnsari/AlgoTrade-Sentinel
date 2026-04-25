from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.features import LabelsData
from app.models.portfolio import Alert
from app.models.signals import Signal
from app.services.market_service import MarketService
from app.services.monitoring_service import get_latest_summary
from app.services.portfolio_service import get_open_positions, latest_orders_for_alerts
from ml.portfolio.alerts_engine import generate_alerts


def ensure_alerts(db: Session) -> None:
    latest_signals = _latest_signal_rows(db)
    latest_orders = [
        {
            "ticker": row.ticker,
            "order_type": row.order_type,
            "order_date": row.order_date,
        }
        for row in latest_orders_for_alerts(db, limit=10)
    ]
    open_positions = [
        {
            "ticker": row.ticker,
            "unrealized_pnl_pct": float(row.unrealized_pnl_pct),
        }
        for row in get_open_positions(db)
    ]
    monitoring_summary = get_latest_summary(db)
    freshness_report = MarketService(db).get_freshness()
    freshness_rows = [
        {
            "ticker": info.ticker,
            "status": info.status,
            "days_stale": info.days_stale,
        }
        for info in freshness_report.tickers.values()
    ]

    generated = generate_alerts(
        latest_signals=latest_signals,
        latest_orders=latest_orders,
        open_positions=open_positions,
        monitoring_summary=monitoring_summary,
        freshness_rows=freshness_rows,
    )

    created = False
    for payload in generated:
        exists = (
            db.query(Alert)
            .filter(
                Alert.alert_type == payload["alert_type"],
                Alert.ticker == payload.get("ticker"),
                Alert.message == payload["message"],
            )
            .first()
        )
        if exists is not None:
            continue
        db.add(
            Alert(
                alert_type=payload["alert_type"],
                ticker=payload.get("ticker"),
                message=payload["message"],
                severity=payload["severity"],
                is_read=False,
            )
        )
        created = True
    if created:
        db.commit()


def list_alerts(
    db: Session,
    *,
    limit: int = 25,
    offset: int = 0,
    severity: str | None = None,
    unread_only: bool = False,
) -> dict[str, Any]:
    ensure_alerts(db)
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if unread_only:
        query = query.filter(Alert.is_read.is_(False))
    total = query.count()
    items = (
        query.order_by(Alert.created_at.desc(), Alert.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": items}


def unread_count(db: Session) -> int:
    ensure_alerts(db)
    return db.query(Alert).filter(Alert.is_read.is_(False)).count()


def mark_read(db: Session, alert_id: int) -> int:
    updated = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return updated


def mark_all_read(db: Session) -> int:
    updated = db.query(Alert).filter(Alert.is_read.is_(False)).update({"is_read": True})
    db.commit()
    return updated


def recent_alerts(db: Session, limit: int = 5) -> list[Alert]:
    ensure_alerts(db)
    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
        .all()
    )


def _latest_signal_rows(db: Session) -> list[dict[str, Any]]:
    signals = db.query(Signal).order_by(Signal.signal_date.desc(), Signal.created_at.desc()).limit(10).all()
    if signals:
        return [
            {
                "ticker": row.ticker,
                "signal": row.signal,
                "signal_date": row.signal_date,
            }
            for row in signals
        ]
    label_rows = (
        db.query(LabelsData)
        .filter(LabelsData.signal_label.isnot(None))
        .order_by(LabelsData.date.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "ticker": row.ticker,
            "signal": row.signal_label,
            "signal_date": row.date,
        }
        for row in label_rows
    ]
