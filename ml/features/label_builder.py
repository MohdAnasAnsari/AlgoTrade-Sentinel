"""
Label builder: forward-looking BUY / SELL / HOLD classification labels.

Input:  OHLCV DataFrame (single ticker, sorted ascending by date).
Output: DataFrame with [ticker, date, future_return_5d, signal_label].
"""
import numpy as np
import pandas as pd

LOOKAHEAD_DAYS = 5
DEFAULT_BUY_THRESHOLD  =  0.02   # +2 %
DEFAULT_SELL_THRESHOLD = -0.02   # -2 %


def compute_labels(
    df: pd.DataFrame,
    buy_threshold: float  = DEFAULT_BUY_THRESHOLD,
    sell_threshold: float = DEFAULT_SELL_THRESHOLD,
) -> pd.DataFrame:
    """
    Compute forward-looking 5-day return and BUY/SELL/HOLD labels.

    Rows in the last LOOKAHEAD_DAYS positions have no future data; their
    signal_label is set to None and must be dropped before training.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)
    c  = df["close"].astype(float)

    future_close = c.shift(-LOOKAHEAD_DAYS)
    df["future_return_5d"] = (future_close - c) / c

    conditions = [
        df["future_return_5d"] > buy_threshold,
        df["future_return_5d"] < sell_threshold,
    ]
    df["signal_label"] = np.select(conditions, ["BUY", "SELL"], default="HOLD")

    # Mark lookahead rows (no future close available) as unlabelled
    df.loc[df["future_return_5d"].isna(), "signal_label"] = None

    return df[["ticker", "date", "future_return_5d", "signal_label"]]


def label_distribution(labels_df: pd.DataFrame) -> dict[str, int]:
    """Returns {BUY, SELL, HOLD} counts for a labelled DataFrame."""
    counts = labels_df["signal_label"].value_counts()
    return {
        "BUY":  int(counts.get("BUY",  0)),
        "SELL": int(counts.get("SELL", 0)),
        "HOLD": int(counts.get("HOLD", 0)),
    }
