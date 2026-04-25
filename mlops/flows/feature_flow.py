"""
Prefect flow: Feature Engineering + Label Building Pipeline

Depends on market data being ingested first (run ingest_flow.py beforehand).
Schedule: daily at 22:00 UTC Mon–Fri (after market close + ingest).
"""
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

from prefect import flow, task

# ── Path setup ────────────────────────────────────────────────────────────
_PROJECT_ROOT = str(Path(__file__).parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(_PROJECT_ROOT) / "backend" / ".env")

from sqlalchemy import create_engine, func, text  # noqa: E402
from sqlalchemy.orm import sessionmaker             # noqa: E402

from ml.features.feature_engineer import compute_features  # noqa: E402
from ml.features.label_builder import compute_labels, label_distribution  # noqa: E402
from ml.features.dataset_builder import build_dataset      # noqa: E402
from ml.data_pipeline.watchlist import get_tickers         # noqa: E402

import pandas as pd                                         # noqa: E402

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_PROJECT_ROOT}/backend/algotrade.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Session = sessionmaker(bind=engine)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@task(retries=2, retry_delay_seconds=10, name="load-ohlcv")
def load_ohlcv(ticker: str) -> pd.DataFrame | None:
    """Query OHLCV rows for one ticker from market_data."""
    with Session() as db:
        rows = db.execute(
            text(
                "SELECT ticker, date, open, high, low, close, adj_close, volume "
                "FROM market_data WHERE ticker = :t ORDER BY date ASC"
            ),
            {"t": ticker},
        ).fetchall()

    if len(rows) < 210:
        logger.warning("%s: %d rows — skipping (need ≥210)", ticker, len(rows))
        return None

    return pd.DataFrame(rows, columns=["ticker", "date", "open", "high", "low",
                                       "close", "adj_close", "volume"])


@task(name="compute-features-task")
def compute_features_task(df: pd.DataFrame) -> pd.DataFrame:
    feat_df = compute_features(df)
    nan_pct = feat_df.drop(columns=["ticker", "date", "close"]).isna().mean().mean() * 100
    logger.info("%s: %d feature rows, %.1f%% NaN", df["ticker"].iloc[0], len(feat_df), nan_pct)
    return feat_df


@task(name="compute-labels-task")
def compute_labels_task(df: pd.DataFrame) -> pd.DataFrame:
    label_df = compute_labels(df)
    dist = label_distribution(label_df.dropna(subset=["signal_label"]))
    logger.info("%s: labels — %s", df["ticker"].iloc[0], dist)
    return label_df


@task(name="store-features-labels")
def store_features_labels(ticker: str, feat_df: pd.DataFrame, label_df: pd.DataFrame) -> None:
    """Upsert computed rows into features_data and labels_data."""
    from ml.features.feature_engineer import ALL_FEATURES

    def _s(v):
        if v is None:
            return None
        try:
            f = float(v)
        except Exception:
            return None
        return None if (f != f) else f

    def _si(v):
        f = _s(v)
        return int(f) if f is not None else None

    with Session() as db:
        db.execute(text("DELETE FROM features_data WHERE ticker = :t"), {"t": ticker})
        db.execute(text("DELETE FROM labels_data   WHERE ticker = :t"), {"t": ticker})

        for _, row in feat_df.iterrows():
            cols = ["ticker", "date", "close"] + ALL_FEATURES
            vals = {
                "ticker": ticker,
                "date":   row["date"],
                "close":  _s(row.get("close")),
            }
            for col in ALL_FEATURES:
                vals[col] = _si(row.get(col)) if col == "obv" else _s(row.get(col))

            placeholders = ", ".join(f":{k}" for k in vals)
            col_names    = ", ".join(vals.keys())
            db.execute(
                text(f"INSERT INTO features_data ({col_names}) VALUES ({placeholders})"),
                vals,
            )

        for _, row in label_df.iterrows():
            ret = _s(row.get("future_return_5d"))
            db.execute(
                text(
                    "INSERT INTO labels_data (ticker, date, future_return_5d, signal_label) "
                    "VALUES (:t, :d, :r, :l)"
                ),
                {"t": ticker, "d": row["date"], "r": ret, "l": row.get("signal_label")},
            )

        db.commit()
    logger.info("%s: stored to DB", ticker)


@task(name="build-dataset-task")
def build_dataset_task(
    all_features: list[pd.DataFrame],
    all_labels: list[pd.DataFrame],
    split_date: str = "2023-01-01",
) -> dict | None:
    if not all_features:
        return None

    feat_combined  = pd.concat(all_features,  ignore_index=True)
    label_combined = pd.concat(all_labels,    ignore_index=True)

    with Session() as db:
        latest = db.execute(text("SELECT MAX(version) FROM dataset_versions")).scalar() or 0
    new_ver = latest + 1

    meta = build_dataset(feat_combined, label_combined, split_date=split_date, version=new_ver)
    logger.info(
        "Dataset v%d: %d rows (train=%d, test=%d), dist=%s",
        new_ver, meta["n_rows"], meta["n_train"], meta["n_test"],
        meta["label_distribution"],
    )

    import json
    from datetime import date as _date

    with Session() as db:
        db.execute(
            text(
                "INSERT INTO dataset_versions "
                "(version, tickers, date_range_start, date_range_end, n_rows, n_train, n_test, "
                " feature_list, label_distribution, split_date, file_path) "
                "VALUES (:v,:t,:ds,:de,:nr,:nt,:ns,:fl,:ld,:sd,:fp)"
            ),
            {
                "v":  new_ver,
                "t":  json.dumps(meta["tickers"]),
                "ds": meta["date_range_start"],
                "de": meta["date_range_end"],
                "nr": meta["n_rows"],
                "nt": meta["n_train"],
                "ns": meta["n_test"],
                "fl": json.dumps(meta["feature_list"]),
                "ld": json.dumps(meta["label_distribution"]),
                "sd": meta["split_date"],
                "fp": meta["file_path"],
            },
        )
        db.commit()

    return meta


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------

@flow(name="feature-engineering-pipeline")
def feature_engineering_pipeline(
    tickers: list[str] | None = None,
    split_date: str = "2023-01-01",
) -> None:
    """
    Main feature engineering flow.

    1. Load OHLCV from DB per ticker
    2. Compute 35 technical features
    3. Compute BUY/SELL/HOLD labels
    4. Store features + labels to DB
    5. Build versioned parquet dataset
    """
    if tickers is None:
        tickers = get_tickers()

    all_features: list[pd.DataFrame] = []
    all_labels:   list[pd.DataFrame] = []

    for ticker in tickers:
        df = load_ohlcv(ticker)
        if df is None:
            continue

        feat_df  = compute_features_task(df)
        label_df = compute_labels_task(df)
        store_features_labels(ticker, feat_df, label_df)

        all_features.append(feat_df)
        all_labels.append(label_df)
        time.sleep(0.1)

    build_dataset_task(all_features, all_labels, split_date=split_date)
    logger.info("Feature engineering pipeline complete for %d tickers", len(all_features))


if __name__ == "__main__":
    feature_engineering_pipeline()
