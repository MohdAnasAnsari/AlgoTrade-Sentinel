"""
Model inference for backtesting.

Loads a trained model + scaler from ml/artifacts/models/{run_id}/
and generates BUY/HOLD/SELL predictions for a features DataFrame.
"""
from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

_ARTIFACTS_DIR = Path(__file__).parents[1] / "artifacts" / "models"
_LABEL_ORDER   = ["BUY", "HOLD", "SELL"]


def generate_predictions(
    run_id:      str,
    features_df: pd.DataFrame,
) -> pd.Series:
    """
    Load model from artifacts and predict signals for each row in features_df.

    features_df must contain a 'date' column + all feature columns the model
    was trained on (stored in features.json alongside the model).

    Returns pd.Series indexed by pd.Timestamp, values 'BUY'/'HOLD'/'SELL'.
    """
    run_dir = _ARTIFACTS_DIR / run_id
    model_path   = run_dir / "model.pkl"
    scaler_path  = run_dir / "scaler.pkl"
    features_path = run_dir / "features.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model artifacts not found: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    feature_names: list[str] = json.loads(features_path.read_text()) \
        if features_path.exists() else []

    df = features_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Use only features the model was trained on; fill missing with 0
    missing = [f for f in feature_names if f not in df.columns]
    if missing:
        logger.warning("Missing features (filling with 0): %s", missing)
        for col in missing:
            df[col] = 0.0

    X = df[feature_names].values.astype(float) if feature_names else df.drop(columns=["date"]).values.astype(float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    X_scaled     = scaler.transform(X)
    preds_int    = model.predict(X_scaled)

    le = LabelEncoder()
    le.fit(_LABEL_ORDER)
    preds_labels = le.inverse_transform(preds_int)

    return pd.Series(preds_labels, index=pd.DatetimeIndex(df["date"].values), name="signal")
