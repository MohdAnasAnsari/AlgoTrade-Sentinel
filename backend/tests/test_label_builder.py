from __future__ import annotations

import pandas as pd

from ml.features.label_builder import compute_labels, label_distribution


def _sample_prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "ticker": ["AAPL"] * len(dates),
            "date": dates,
            "close": [100, 103, 106, 108, 109, 111, 107, 105, 102, 100],
        }
    )


def test_compute_labels_assigns_buy_and_sell_classes() -> None:
    labels = compute_labels(_sample_prices(), buy_threshold=0.02, sell_threshold=-0.02)
    assert "BUY" in set(labels["signal_label"].dropna())
    assert "SELL" in set(labels["signal_label"].dropna())


def test_compute_labels_marks_final_lookahead_rows_unlabelled() -> None:
    labels = compute_labels(_sample_prices())
    assert labels.tail(5)["signal_label"].isna().all()


def test_label_distribution_counts_each_class() -> None:
    labels = compute_labels(_sample_prices(), buy_threshold=0.02, sell_threshold=-0.02)
    distribution = label_distribution(labels.dropna())
    assert distribution["BUY"] >= 1
    assert distribution["SELL"] >= 1


def test_compute_labels_respects_custom_thresholds() -> None:
    labels = compute_labels(_sample_prices(), buy_threshold=0.20, sell_threshold=-0.20)
    assert set(labels["signal_label"].dropna()) == {"HOLD"}
