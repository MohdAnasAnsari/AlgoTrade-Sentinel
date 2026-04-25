"""
Batch inference pipeline for AlgoTrade Sentinel.

Loads the champion model (Production stage) from MLflow Model Registry,
generates BUY/SELL/HOLD predictions with probabilities and explanations
for all watchlist tickers.
"""
from __future__ import annotations

import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ml.training.mlflow_logger import get_default_uri, REGISTERED_MODEL_NAME  # noqa: E402
from ml.features.feature_engineer import ALL_FEATURES                          # noqa: E402

_ARTIFACTS_DIR = _PROJECT_ROOT / "ml" / "artifacts" / "models"
LABEL_ORDER    = ["BUY", "HOLD", "SELL"]
CONFIDENCE_THRESHOLD = 0.55


# ---------------------------------------------------------------------------
# Champion model loading
# ---------------------------------------------------------------------------

def load_champion_artifacts(model_name: str = REGISTERED_MODEL_NAME) -> tuple:
    """
    Load champion model, scaler, features list, and run_id from disk artifacts.
    Returns (model, scaler, feature_names, run_id, model_version).
    Raises RuntimeError if no Production version found.
    """
    import mlflow
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(get_default_uri())
    client = MlflowClient()

    versions = client.get_latest_versions(model_name, stages=["Production"])
    if not versions:
        # Fall back to Staging if no Production model yet
        versions = client.get_latest_versions(model_name, stages=["Staging"])
        if not versions:
            raise RuntimeError(f"No Production or Staging model found for '{model_name}'")
        logger.warning("No Production model — falling back to Staging v%s", versions[0].version)

    mv     = versions[0]
    run_id = mv.run_id
    version = mv.version

    run_dir = _ARTIFACTS_DIR / run_id
    model_pkl  = run_dir / "model.pkl"
    scaler_pkl = run_dir / "scaler.pkl"
    feat_json  = run_dir / "features.json"

    if not model_pkl.exists():
        raise RuntimeError(f"Model artifacts not found at {run_dir}")

    with open(model_pkl, "rb") as f:
        model = pickle.load(f)
    with open(scaler_pkl, "rb") as f:
        scaler = pickle.load(f)
    feature_names = json.loads(feat_json.read_text()) if feat_json.exists() else ALL_FEATURES

    logger.info("Loaded champion model from run %s v%s", run_id, version)
    return model, scaler, feature_names, run_id, version


# ---------------------------------------------------------------------------
# Signal generation
# ---------------------------------------------------------------------------

def generate_signals_for_ticker(
    ticker: str,
    features_df: pd.DataFrame,
    model,
    scaler,
    feature_names: list[str],
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> list[dict]:
    """
    Generate signals for a single ticker given a features DataFrame.
    Returns list of signal dicts (only rows with confidence >= threshold).
    """
    if features_df.empty:
        return []

    available_cols = [c for c in feature_names if c in features_df.columns]
    X_raw = features_df[available_cols].values.astype(float)

    # Scale using all expected feature positions (pad missing with 0)
    if len(available_cols) < len(feature_names):
        X_full = np.zeros((len(X_raw), len(feature_names)))
        idx_map = [feature_names.index(c) for c in available_cols]
        X_full[:, idx_map] = X_raw
        X_raw = X_full

    X = scaler.transform(X_raw)

    labels = model.predict(X)
    if hasattr(model, "predict_proba"):
        probas = model.predict_proba(X)
    else:
        n = len(X)
        probas = np.zeros((n, len(LABEL_ORDER)))
        for i, lbl in enumerate(labels):
            probas[i, lbl] = 1.0

    # Map numeric labels back to BUY/HOLD/SELL
    model_classes = getattr(model, "classes_", list(range(len(LABEL_ORDER))))

    signals = []
    dates = features_df.index if isinstance(features_df.index, pd.DatetimeIndex) \
            else pd.to_datetime(features_df.get("date", features_df.index))

    for i, (date, label_enc, proba_row) in enumerate(zip(dates, labels, probas)):
        # Map encoded label to class position in LABEL_ORDER
        if label_enc < len(model_classes):
            label_idx = int(model_classes[label_enc])
        else:
            label_idx = int(label_enc)
        signal_str = LABEL_ORDER[label_idx] if label_idx < len(LABEL_ORDER) else "HOLD"

        # Align probabilities with LABEL_ORDER
        prob_map = {}
        for ci, cls in enumerate(model_classes):
            if int(cls) < len(LABEL_ORDER):
                prob_map[LABEL_ORDER[int(cls)]] = float(proba_row[ci]) if ci < len(proba_row) else 0.0
        prob_buy  = prob_map.get("BUY",  0.0)
        prob_sell = prob_map.get("SELL", 0.0)
        prob_hold = prob_map.get("HOLD", 0.0)

        confidence = max(prob_buy, prob_sell, prob_hold)

        if confidence < confidence_threshold:
            continue

        explanation = _build_explanation(
            features_df.iloc[i] if len(features_df) > i else pd.Series(),
            available_cols,
            signal_str,
        )

        signals.append({
            "ticker":       ticker,
            "signal_date":  date.date() if hasattr(date, "date") else str(date)[:10],
            "signal":       signal_str,
            "confidence":   round(confidence, 4),
            "prob_buy":     round(prob_buy,  4),
            "prob_sell":    round(prob_sell, 4),
            "prob_hold":    round(prob_hold, 4),
            "explanation":  explanation,
        })

    return signals


def _build_explanation(row: pd.Series, feature_names: list[str], signal: str) -> str:
    """Return top 3 feature names + values as a human-readable explanation string."""
    # Priority features per signal direction
    priority = {
        "BUY":  ["rsi_14", "macd_hist", "price_vs_sma20_pct", "return_5d", "bb_pct_b"],
        "SELL": ["rsi_14", "macd_hist", "price_vs_sma20_pct", "max_drawdown", "return_5d"],
        "HOLD": ["daily_volatility", "adx_14", "hist_vol_20", "bb_width", "vol_ratio"],
    }
    top_names = [f for f in priority.get(signal, []) if f in feature_names][:3]
    if not top_names:
        top_names = feature_names[:3]

    parts = []
    for feat in top_names:
        val = row.get(feat)
        if val is not None and not pd.isna(val):
            parts.append(f"{feat}={float(val):.3f}")
    return "; ".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_batch_inference(
    features_per_ticker: dict[str, pd.DataFrame],
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    model_name: str = REGISTERED_MODEL_NAME,
) -> dict:
    """
    Run batch inference across all tickers.

    Args:
        features_per_ticker: {ticker: features_df} where features_df has
                             feature columns and DatetimeIndex or 'date' column.
        confidence_threshold: Minimum confidence to emit a signal.
        model_name: Registered MLflow model name.

    Returns:
        {
          "signals": [signal_dict, ...],
          "model_run_id": str,
          "model_version": str,
          "tickers_processed": [str, ...],
          "tickers_skipped": [str, ...],
          "total_signals": int,
        }
    """
    model, scaler, feature_names, run_id, version = load_champion_artifacts(model_name)

    all_signals: list[dict] = []
    processed:   list[str]  = []
    skipped:     list[str]  = []

    for ticker, feat_df in features_per_ticker.items():
        if feat_df is None or feat_df.empty:
            skipped.append(ticker)
            continue
        try:
            sigs = generate_signals_for_ticker(
                ticker, feat_df, model, scaler, feature_names, confidence_threshold,
            )
            all_signals.extend(sigs)
            processed.append(ticker)
            logger.info("  %s → %d signals (confidence ≥ %.2f)", ticker, len(sigs), confidence_threshold)
        except Exception as exc:
            logger.error("Inference failed for %s: %s", ticker, exc)
            skipped.append(ticker)

    return {
        "signals":           all_signals,
        "model_run_id":      run_id,
        "model_version":     version,
        "tickers_processed": processed,
        "tickers_skipped":   skipped,
        "total_signals":     len(all_signals),
    }
