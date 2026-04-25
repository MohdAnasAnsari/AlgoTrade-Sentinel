from __future__ import annotations

from typing import Any


def generate_alerts(
    *,
    latest_signals: list[dict[str, Any]],
    latest_orders: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    monitoring_summary: dict[str, Any] | None,
    freshness_rows: list[dict[str, Any]],
    profit_target_pct: float = 5.0,
    stop_loss_pct: float = -3.0,
    drift_threshold: float = 30.0,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for signal in latest_signals[:10]:
        alerts.append(
            {
                "alert_type": "NEW_SIGNAL",
                "ticker": signal.get("ticker"),
                "message": f"{signal.get('ticker')} produced a {signal.get('signal')} signal.",
                "severity": "INFO",
            }
        )

    for order in latest_orders[:10]:
        alerts.append(
            {
                "alert_type": "POSITION_OPENED" if order.get("order_type") == "BUY" else "POSITION_CLOSED",
                "ticker": order.get("ticker"),
                "message": f"{order.get('order_type')} order executed for {order.get('ticker')}.",
                "severity": "INFO",
            }
        )

    for position in open_positions:
        pnl_pct = float(position.get("unrealized_pnl_pct") or 0.0)
        if pnl_pct >= profit_target_pct:
            alerts.append(
                {
                    "alert_type": "PROFIT_TARGET",
                    "ticker": position.get("ticker"),
                    "message": f"{position.get('ticker')} is up {pnl_pct:.2f}% and crossed the profit target.",
                    "severity": "INFO",
                }
            )
        if pnl_pct <= stop_loss_pct:
            alerts.append(
                {
                    "alert_type": "STOP_LOSS",
                    "ticker": position.get("ticker"),
                    "message": f"{position.get('ticker')} is down {pnl_pct:.2f}% and crossed the stop-loss threshold.",
                    "severity": "WARN",
                }
            )

    if monitoring_summary:
        if monitoring_summary.get("alert_level") == "CRITICAL":
            alerts.append(
                {
                    "alert_type": "MODEL_DEGRADED",
                    "ticker": None,
                    "message": "Monitoring status is CRITICAL and model behavior should be reviewed.",
                    "severity": "CRITICAL",
                }
            )
        drift_share = float(monitoring_summary.get("drift_share") or 0.0)
        if drift_share > drift_threshold:
            alerts.append(
                {
                    "alert_type": "DRIFT_DETECTED",
                    "ticker": None,
                    "message": f"Feature drift share reached {drift_share:.2f}%.",
                    "severity": "WARN" if drift_share < 50 else "CRITICAL",
                }
            )

    for row in freshness_rows:
        if row.get("status") == "stale":
            alerts.append(
                {
                    "alert_type": "DATA_STALE",
                    "ticker": row.get("ticker"),
                    "message": f"{row.get('ticker')} market data is stale by {row.get('days_stale') or '?'} day(s).",
                    "severity": "WARN",
                }
            )

    return alerts
