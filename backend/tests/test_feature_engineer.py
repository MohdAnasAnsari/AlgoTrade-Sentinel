from __future__ import annotations

import pandas as pd

from ml.features.feature_engineer import ALL_FEATURES, compute_features


def _sample_ohlcv() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=220, freq="D")
    base = pd.Series(range(220), dtype=float)
    return pd.DataFrame(
        {
            "ticker": ["AAPL"] * len(dates),
            "date": dates,
            "open": 100 + base,
            "high": 101 + base,
            "low": 99 + base,
            "close": 100.5 + base,
            "adj_close": 100.5 + base,
            "volume": 1_000_000 + base * 10,
        }
    )


def test_compute_features_includes_catalogued_columns() -> None:
    features = compute_features(_sample_ohlcv())
    assert all(column in features.columns for column in ALL_FEATURES)


def test_compute_features_preserves_row_count() -> None:
    df = _sample_ohlcv()
    features = compute_features(df)
    assert len(features) == len(df)


def test_compute_features_computes_sma_10() -> None:
    features = compute_features(_sample_ohlcv())
    expected = sum(100.5 + idx for idx in range(10)) / 10
    assert round(float(features.iloc[9]["sma_10"]), 4) == round(expected, 4)


def test_compute_features_generates_positive_bollinger_width_after_warmup() -> None:
    features = compute_features(_sample_ohlcv())
    assert float(features.iloc[40]["bb_width"]) > 0


def test_compute_features_obv_accumulates_with_uptrend() -> None:
    features = compute_features(_sample_ohlcv())
    assert int(features.iloc[-1]["obv"]) > 0
