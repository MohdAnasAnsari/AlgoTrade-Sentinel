from __future__ import annotations

import pandas as pd
import pytest

from ml.backtesting.backtest_engine import run_backtest


def _sample_prices() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    return pd.DataFrame({"date": dates, "close": [100, 101, 103, 102, 104, 106]})


def _sample_predictions() -> pd.Series:
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    return pd.Series(["BUY", "HOLD", "HOLD", "SELL", "BUY", "HOLD"], index=dates)


def test_backtest_returns_metrics_and_curves() -> None:
    result = run_backtest(_sample_prices(), _sample_predictions(), initial_capital=10_000)
    assert "metrics" in result
    assert len(result["equity_curve"]) == 6


def test_backtest_creates_trade_records() -> None:
    result = run_backtest(_sample_prices(), _sample_predictions(), initial_capital=10_000)
    assert len(result["trades"]) >= 1
    assert result["metrics"]["total_trades"] >= 1


def test_backtest_uses_buy_and_hold_benchmark_when_spy_missing() -> None:
    result = run_backtest(_sample_prices(), _sample_predictions(), spy_prices=None, initial_capital=10_000)
    assert all(point["benchmark"] is not None for point in result["equity_curve"])


def test_backtest_closes_open_trade_at_end_of_period() -> None:
    dates = pd.date_range("2025-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"date": dates, "close": [100, 102, 104, 105]})
    predictions = pd.Series(["BUY", "HOLD", "HOLD", "HOLD"], index=dates)
    result = run_backtest(prices, predictions, initial_capital=10_000)
    assert result["trades"][-1]["exit_date"] == "2025-01-04"


def test_backtest_raises_when_prices_empty() -> None:
    with pytest.raises(ValueError):
        run_backtest(pd.DataFrame({"date": [], "close": []}), pd.Series(dtype=str))
