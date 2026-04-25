"""
Core backtesting engine for AlgoTrade Sentinel.

Pure logic — no DB, no MLflow, no I/O.
Inputs: price DataFrame, predictions Series, optional benchmark prices.
Outputs: dict with metrics, equity_curve, drawdown, trades, monthly_returns.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RF_ANNUAL   = 0.04   # 4% annual risk-free rate
TRADING_DAYS = 252


def run_backtest(
    prices:            pd.DataFrame,
    predictions:       pd.Series,
    spy_prices:        Optional[pd.DataFrame] = None,
    initial_capital:   float = 100_000.0,
    transaction_cost:  float = 0.001,
    slippage:          float = 0.0005,
    position_frac:     float = 0.10,
) -> dict:
    """
    Run event-driven backtest and return all results.

    prices:       DataFrame with columns ['date', 'close'] sorted ascending.
                  'date' column may be str, date, or Timestamp.
    predictions:  Series indexed by pd.Timestamp → 'BUY' | 'HOLD' | 'SELL'.
    spy_prices:   Optional benchmark price DataFrame with same format.
    """
    # ── Normalise price data ────────────────────────────────────────────────
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices.sort_values("date").reset_index(drop=True)
    prices = prices.dropna(subset=["close"])
    if prices.empty:
        raise ValueError("No price data available for backtest period")

    # Normalise prediction index
    pred_index = pd.DatetimeIndex(predictions.index)
    predictions = pd.Series(predictions.values, index=pred_index)

    # ── Portfolio state ─────────────────────────────────────────────────────
    cash             = float(initial_capital)
    shares           = 0.0
    entry_price_adj  = 0.0
    entry_total_cost = 0.0
    entry_date       = None

    equity_curve: list[dict] = []
    trades:        list[dict] = []

    for _, row in prices.iterrows():
        dt    = row["date"]
        close = float(row["close"])
        signal = predictions.get(dt, "HOLD") or "HOLD"

        # ── BUY ───────────────────────────────────────────────────────────
        if signal == "BUY" and shares == 0.0:
            buy_px   = close * (1.0 + slippage)
            max_spend = cash * position_frac
            n_shares = max_spend / (buy_px * (1.0 + transaction_cost))
            cost     = n_shares * buy_px * (1.0 + transaction_cost)
            if cost > 0.01 and cost <= cash:
                cash            -= cost
                shares           = n_shares
                entry_price_adj  = buy_px
                entry_total_cost = cost
                entry_date       = dt

        # ── SELL ──────────────────────────────────────────────────────────
        elif signal == "SELL" and shares > 0.0:
            sell_px  = close * (1.0 - slippage)
            proceeds = shares * sell_px * (1.0 - transaction_cost)
            pnl      = proceeds - entry_total_cost
            ret_pct  = pnl / entry_total_cost * 100.0 if entry_total_cost > 0 else 0.0
            holding  = (dt - entry_date).days if entry_date else 0

            trades.append({
                "entry_date":   entry_date.strftime("%Y-%m-%d") if entry_date else "",
                "exit_date":    dt.strftime("%Y-%m-%d"),
                "entry_price":  round(entry_price_adj, 4),
                "exit_price":   round(sell_px, 4),
                "shares":       round(shares, 4),
                "pnl":          round(pnl, 2),
                "return_pct":   round(ret_pct, 4),
                "holding_days": int(holding),
            })
            cash            += proceeds
            shares           = 0.0
            entry_price_adj  = 0.0
            entry_total_cost = 0.0
            entry_date       = None

        portfolio_val = cash + shares * close
        equity_curve.append({
            "date":      dt.strftime("%Y-%m-%d"),
            "value":     round(portfolio_val, 2),
            "benchmark": None,
        })

    # Close any open position at period end
    if shares > 0.0:
        last_row = prices.iloc[-1]
        last_close = float(last_row["close"])
        sell_px  = last_close * (1.0 - slippage)
        proceeds = shares * sell_px * (1.0 - transaction_cost)
        pnl      = proceeds - entry_total_cost
        ret_pct  = pnl / entry_total_cost * 100.0 if entry_total_cost > 0 else 0.0
        last_dt  = last_row["date"]
        holding  = (last_dt - entry_date).days if entry_date else 0
        trades.append({
            "entry_date":   entry_date.strftime("%Y-%m-%d") if entry_date else "",
            "exit_date":    last_dt.strftime("%Y-%m-%d"),
            "entry_price":  round(entry_price_adj, 4),
            "exit_price":   round(sell_px, 4),
            "shares":       round(shares, 4),
            "pnl":          round(pnl, 2),
            "return_pct":   round(ret_pct, 4),
            "holding_days": int(holding),
        })

    # ── Equity series ───────────────────────────────────────────────────────
    eq_idx    = pd.to_datetime([e["date"] for e in equity_curve])
    eq_vals   = pd.Series([e["value"] for e in equity_curve], index=eq_idx, dtype=float)
    n_days    = len(eq_vals)

    # ── Benchmark equity curve ──────────────────────────────────────────────
    spy_map: dict[pd.Timestamp, float] = {}
    if spy_prices is not None and not spy_prices.empty:
        sp = spy_prices.copy()
        sp["date"] = pd.to_datetime(sp["date"])
        sp = sp.sort_values("date")
        sp = sp[(sp["date"] >= prices.iloc[0]["date"]) &
                (sp["date"] <= prices.iloc[-1]["date"])]
        if not sp.empty:
            spy_start = float(sp.iloc[0]["close"])
            spy_map   = {row["date"]: initial_capital * float(row["close"]) / spy_start
                         for _, row in sp.iterrows()}

    # Fallback: ticker buy-and-hold
    if not spy_map:
        first_close = float(prices.iloc[0]["close"])
        spy_map = {row["date"]: initial_capital * float(row["close"]) / first_close
                   for _, row in prices.iterrows()}

    spy_keys = sorted(spy_map.keys())

    def _nearest_bench(dt: pd.Timestamp) -> float:
        if not spy_keys:
            return float(initial_capital)
        closest = min(spy_keys, key=lambda d: abs((d - dt).total_seconds()))
        return spy_map[closest]

    for e in equity_curve:
        dt = pd.Timestamp(e["date"])
        e["benchmark"] = round(spy_map.get(dt, _nearest_bench(dt)), 2)

    bench_series = pd.Series(
        {pd.Timestamp(e["date"]): e["benchmark"] for e in equity_curve},
        dtype=float,
    )

    # ── Return metrics ──────────────────────────────────────────────────────
    final_val      = float(eq_vals.iloc[-1])
    total_return   = (final_val - initial_capital) / initial_capital * 100.0
    ann_factor     = TRADING_DAYS / max(n_days, 1)
    ann_return     = ((1.0 + total_return / 100.0) ** ann_factor - 1.0) * 100.0

    bench_final    = float(bench_series.iloc[-1]) if not bench_series.empty else initial_capital
    bench_total    = (bench_final - initial_capital) / initial_capital * 100.0
    bench_ann      = ((1.0 + bench_total / 100.0) ** ann_factor - 1.0) * 100.0
    alpha          = ann_return - bench_ann

    # ── Risk metrics ────────────────────────────────────────────────────────
    daily_rets  = eq_vals.pct_change().dropna()
    rf_daily    = RF_ANNUAL / TRADING_DAYS

    vol_ann     = float(daily_rets.std()) * math.sqrt(TRADING_DAYS) * 100.0

    excess      = daily_rets - rf_daily
    sharpe      = float(excess.mean() / excess.std() * math.sqrt(TRADING_DAYS)) \
                  if float(excess.std()) > 1e-10 else 0.0

    downside    = daily_rets[daily_rets < rf_daily] - rf_daily
    down_std    = math.sqrt(float((downside ** 2).mean())) if len(downside) > 0 else 1e-10
    sortino     = float((daily_rets.mean() - rf_daily) / down_std * math.sqrt(TRADING_DAYS))

    rolling_max = eq_vals.expanding().max()
    dd_series   = (eq_vals - rolling_max) / rolling_max * 100.0
    max_dd      = float(dd_series.min())

    calmar      = ann_return / abs(max_dd) if abs(max_dd) > 1e-6 else 0.0

    # ── Trade metrics ───────────────────────────────────────────────────────
    total_trades = len(trades)
    if total_trades > 0:
        wins  = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate  = len(wins) / total_trades * 100.0
        avg_win   = sum(t["return_pct"] for t in wins)   / len(wins)   if wins   else 0.0
        avg_loss  = sum(t["return_pct"] for t in losses) / len(losses) if losses else 0.0
        gross_p   = sum(t["pnl"] for t in wins)
        gross_l   = abs(sum(t["pnl"] for t in losses))
        profit_f  = gross_p / gross_l if gross_l > 0 else (99.0 if gross_p > 0 else 1.0)
        avg_hold  = sum(t["holding_days"] for t in trades) / total_trades
    else:
        win_rate = avg_win = avg_loss = profit_f = avg_hold = 0.0

    # ── Drawdown series ─────────────────────────────────────────────────────
    drawdown_data = [
        {"date": dt.strftime("%Y-%m-%d"), "drawdown": round(float(v), 4)}
        for dt, v in dd_series.items()
    ]

    # ── Monthly returns ─────────────────────────────────────────────────────
    eq_monthly  = eq_vals.resample("ME").last()
    monthly_pct = eq_monthly.pct_change() * 100.0
    monthly_returns = {
        dt.strftime("%Y-%m"): round(float(v), 4)
        for dt, v in monthly_pct.items()
        if not math.isnan(v)
    }

    metrics = {
        "total_return":      round(total_return, 4),
        "annualized_return": round(ann_return, 4),
        "benchmark_return":  round(bench_total, 4),
        "alpha":             round(alpha, 4),
        "max_drawdown":      round(max_dd, 4),
        "sharpe_ratio":      round(sharpe, 4),
        "sortino_ratio":     round(sortino, 4),
        "calmar_ratio":      round(calmar, 4),
        "daily_volatility":  round(vol_ann, 4),
        "total_trades":      total_trades,
        "win_rate":          round(win_rate, 4),
        "avg_win":           round(avg_win, 4),
        "avg_loss":          round(avg_loss, 4),
        "profit_factor":     round(profit_f, 4),
        "avg_holding_days":  round(avg_hold, 2),
    }

    return {
        "metrics":         metrics,
        "equity_curve":    equity_curve,
        "drawdown":        drawdown_data,
        "trades":          trades,
        "monthly_returns": monthly_returns,
    }
