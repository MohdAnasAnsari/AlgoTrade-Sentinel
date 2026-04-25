"""
Dataset builder: joins features + labels, applies time-aware train/test split,
exports versioned parquet file and JSON metadata sidecar.

No data leakage: split is strictly temporal (no random shuffle).
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from ml.features.feature_engineer import ALL_FEATURES

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parents[1] / "artifacts" / "datasets"
DEFAULT_SPLIT_DATE = "2023-01-01"


def build_dataset(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    split_date: str = DEFAULT_SPLIT_DATE,
    version: Optional[int] = None,
    output_dir: Optional[Path] = None,
    buy_threshold: float = 0.02,
    sell_threshold: float = -0.02,
) -> dict:
    """
    Join features + labels → drop NaN / lookahead rows → time-split → export.

    Returns a metadata dict suitable for storing in the dataset_versions table.
    """
    out_dir = Path(output_dir) if output_dir else ARTIFACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if version is None:
        existing = sorted(out_dir.glob("dataset_v*.parquet"))
        version  = len(existing) + 1

    # ── Join ──────────────────────────────────────────────────────────────
    df = features_df.merge(
        labels_df[["ticker", "date", "future_return_5d", "signal_label"]],
        on=["ticker", "date"],
        how="inner",
    )

    # ── Drop unlabelled lookahead rows ───────────────────────────────────
    df = df.dropna(subset=["signal_label"])

    # ── Drop rows where any feature is NaN (indicator warm-up) ───────────
    available_features = [c for c in ALL_FEATURES if c in df.columns]
    df = df.dropna(subset=available_features)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # ── Temporal split (no shuffle — preserves time-series integrity) ─────
    split_dt = pd.to_datetime(split_date)
    train    = df[df["date"] < split_dt]
    test     = df[df["date"] >= split_dt]

    # ── Label distribution ────────────────────────────────────────────────
    counts = df["signal_label"].value_counts()
    dist = {
        "BUY":  int(counts.get("BUY",  0)),
        "SELL": int(counts.get("SELL", 0)),
        "HOLD": int(counts.get("HOLD", 0)),
    }

    # ── Export parquet ────────────────────────────────────────────────────
    file_path = out_dir / f"dataset_v{version}.parquet"
    df.to_parquet(file_path, index=False)
    logger.info("Saved dataset v%d → %s (%d rows)", version, file_path, len(df))

    # ── Metadata ──────────────────────────────────────────────────────────
    tickers = sorted(df["ticker"].unique().tolist())
    metadata = {
        "version":          version,
        "tickers":          tickers,
        "date_range_start": df["date"].min().date().isoformat(),
        "date_range_end":   df["date"].max().date().isoformat(),
        "n_rows":           len(df),
        "n_train":          len(train),
        "n_test":           len(test),
        "feature_list":     available_features,
        "label_distribution": dist,
        "split_date":       split_date,
        "file_path":        str(file_path),
        "created_at":       datetime.utcnow().isoformat(),
    }

    meta_path = out_dir / f"dataset_v{version}_meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    logger.info("Metadata → %s", meta_path)

    return metadata
