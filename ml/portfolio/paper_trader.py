from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class PortfolioConfig:
    initial_cash: float = 100_000.0
    max_positions: int = 5
    transaction_cost: float = 0.001


def simulate_paper_portfolio(
    market_rows: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
    watchlist: dict[str, dict[str, str]],
    config: PortfolioConfig | None = None,
) -> dict[str, list[dict[str, Any]]]:
    cfg = config or PortfolioConfig()
    grouped_market: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_dates: dict[str, list[date]] = {}
    close_lookup: dict[tuple[str, date], float] = {}
    open_lookup: dict[tuple[str, date], float] = {}

    for row in sorted(market_rows, key=lambda item: (item["date"], item["ticker"])):
        grouped_market[row["ticker"]].append(row)
        close_lookup[(row["ticker"], row["date"])] = float(row["close"])
        open_lookup[(row["ticker"], row["date"])] = float(row["open"])

    for ticker, rows in grouped_market.items():
        grouped_dates[ticker] = [row["date"] for row in rows]

    scheduled_events: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for signal in sorted(signal_rows, key=lambda item: (item["signal_date"], item["ticker"])):
        ticker = signal["ticker"]
        dates = grouped_dates.get(ticker, [])
        if not dates:
            continue
        idx = bisect_right(dates, signal["signal_date"])
        if idx >= len(dates):
            continue
        execution_date = dates[idx]
        price = open_lookup.get((ticker, execution_date))
        if price is None:
            continue
        scheduled_events[execution_date].append(
            {
                "ticker": ticker,
                "action": str(signal["signal"]).upper(),
                "signal_id": signal.get("signal_id"),
                "execution_date": execution_date,
                "execution_price": float(price),
            }
        )

    trade_calendar = sorted({row["date"] for row in market_rows})
    latest_close: dict[str, float] = {}
    cash = float(cfg.initial_cash)
    realized_pnl = 0.0
    open_positions: dict[str, dict[str, Any]] = {}
    closed_positions: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []

    market_rows_by_date: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in market_rows:
        market_rows_by_date[row["date"]].append(row)

    for trade_date in trade_calendar:
        for row in market_rows_by_date[trade_date]:
            latest_close[row["ticker"]] = float(row["close"])

        for event in sorted(scheduled_events.get(trade_date, []), key=lambda item: (item["ticker"], item["action"])):
            ticker = event["ticker"]
            action = event["action"]
            price = float(event["execution_price"])
            info = watchlist.get(ticker, {})

            if action == "BUY":
                if ticker in open_positions or len(open_positions) >= cfg.max_positions:
                    continue
                available_slots = max(cfg.max_positions - len(open_positions), 1)
                allocation = cash / available_slots
                shares = allocation / (price * (1.0 + cfg.transaction_cost)) if price > 0 else 0.0
                gross_value = shares * price
                fee = gross_value * cfg.transaction_cost
                total_cost = gross_value + fee
                if shares <= 0 or total_cost <= 0 or total_cost > cash:
                    continue

                cash -= total_cost
                open_positions[ticker] = {
                    "ticker": ticker,
                    "entry_date": trade_date,
                    "entry_price": price,
                    "shares": shares,
                    "cost_basis": total_cost,
                    "company_name": info.get("company_name") or info.get("name"),
                    "sector": info.get("sector"),
                }
                orders.append(
                    {
                        "ticker": ticker,
                        "order_date": trade_date,
                        "order_type": "BUY",
                        "price": price,
                        "shares": shares,
                        "total_value": gross_value,
                        "transaction_cost": fee,
                        "signal_id": event.get("signal_id"),
                    }
                )

            elif action == "SELL":
                position = open_positions.get(ticker)
                if position is None:
                    continue
                gross_value = position["shares"] * price
                fee = gross_value * cfg.transaction_cost
                net_proceeds = gross_value - fee
                realized = net_proceeds - float(position["cost_basis"])
                realized_pnl += realized
                cash += net_proceeds

                closed_positions.append(
                    {
                        "ticker": ticker,
                        "entry_date": position["entry_date"],
                        "entry_price": position["entry_price"],
                        "shares": position["shares"],
                        "current_price": price,
                        "market_value": 0.0,
                        "unrealized_pnl": 0.0,
                        "unrealized_pnl_pct": 0.0,
                        "status": "CLOSED",
                        "company_name": position.get("company_name"),
                        "sector": position.get("sector"),
                    }
                )
                orders.append(
                    {
                        "ticker": ticker,
                        "order_date": trade_date,
                        "order_type": "SELL",
                        "price": price,
                        "shares": position["shares"],
                        "total_value": gross_value,
                        "transaction_cost": fee,
                        "signal_id": event.get("signal_id"),
                    }
                )
                del open_positions[ticker]

        invested_value = 0.0
        unrealized_pnl = 0.0
        for ticker, position in open_positions.items():
            current_price = latest_close.get(ticker, float(position["entry_price"]))
            market_value = position["shares"] * current_price
            pnl = market_value - float(position["cost_basis"])
            pnl_pct = (pnl / float(position["cost_basis"]) * 100.0) if position["cost_basis"] else 0.0
            position["current_price"] = current_price
            position["market_value"] = market_value
            position["unrealized_pnl"] = pnl
            position["unrealized_pnl_pct"] = pnl_pct
            invested_value += market_value
            unrealized_pnl += pnl

        total_value = cash + invested_value
        total_pnl = realized_pnl + unrealized_pnl
        total_pnl_pct = ((total_value / cfg.initial_cash) - 1.0) * 100.0 if cfg.initial_cash else 0.0
        snapshots.append(
            {
                "snapshot_date": trade_date,
                "total_value": total_value,
                "cash_balance": cash,
                "invested_value": invested_value,
                "total_pnl": total_pnl,
                "total_pnl_pct": total_pnl_pct,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
            }
        )

    open_position_rows = [
        {
            "ticker": ticker,
            "entry_date": position["entry_date"],
            "entry_price": position["entry_price"],
            "shares": position["shares"],
            "current_price": position.get("current_price"),
            "market_value": position.get("market_value", 0.0),
            "unrealized_pnl": position.get("unrealized_pnl", 0.0),
            "unrealized_pnl_pct": position.get("unrealized_pnl_pct", 0.0),
            "status": "OPEN",
            "company_name": position.get("company_name"),
            "sector": position.get("sector"),
        }
        for ticker, position in sorted(open_positions.items())
    ]

    return {
        "positions": closed_positions + open_position_rows,
        "orders": orders,
        "snapshots": snapshots,
    }
