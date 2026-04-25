"""
Feature service: orchestrates feature engineering, label building,
and dataset versioning via the backend ORM.

ML computation functions are imported from ml/ (project root on sys.path).
"""
import json
import logging
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import func, insert
from sqlalchemy.orm import Session

# ── ML imports (project root → ml/) ────────────────────────────────────────
_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ml.features.feature_engineer import ALL_FEATURES, FEATURE_GROUPS, compute_features  # noqa: E402
from ml.features.label_builder import compute_labels  # noqa: E402
from ml.features.dataset_builder import build_dataset  # noqa: E402

from app.models.market import MarketData
from app.models.features import DatasetVersion, FeaturesData, LabelsData
from app.schemas.features import (
    DatasetVersionInfo,
    FeatureListResponse,
    FeatureRow,
    FeatureStat,
    FeatureStatsResponse,
    LabelDistribution,
    PipelineRunResponse,
)
from app.services.market_service import get_watchlist_tickers

logger = logging.getLogger(__name__)

# Numeric precision guard: cap extreme floats before storing
_MAX_NUMERIC = 1e12


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if f != f or abs(f) > _MAX_NUMERIC:   # NaN or Inf
        return None
    return f


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if f != f:
        return None
    return int(f)


# ---------------------------------------------------------------------------
# Feature Service
# ---------------------------------------------------------------------------

class FeatureService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def run_pipeline(
        self,
        tickers: list[str] | None = None,
        split_date: str = "2023-01-01",
        build_ds: bool = True,
    ) -> PipelineRunResponse:
        if tickers is None:
            tickers = get_watchlist_tickers()

        all_features: list[pd.DataFrame] = []
        all_labels:   list[pd.DataFrame] = []
        processed: list[str] = []
        skipped:   list[str] = []

        for ticker in tickers:
            rows = (
                self.db.query(MarketData)
                .filter(MarketData.ticker == ticker)
                .order_by(MarketData.date.asc())
                .all()
            )
            if len(rows) < 210:   # need at least SMA200 warmup
                logger.warning("%s: only %d rows — skipping", ticker, len(rows))
                skipped.append(ticker)
                continue

            df = pd.DataFrame(
                [
                    {
                        "ticker":   r.ticker,
                        "date":     r.date,
                        "open":     float(r.open)  if r.open  else None,
                        "high":     float(r.high)  if r.high  else None,
                        "low":      float(r.low)   if r.low   else None,
                        "close":    float(r.close) if r.close else None,
                        "adj_close": float(r.adj_close) if r.adj_close else None,
                        "volume":   float(r.volume) if r.volume else 0.0,
                    }
                    for r in rows
                ]
            )

            try:
                feat_df  = compute_features(df)
                label_df = compute_labels(df)
            except Exception as exc:
                logger.error("%s: computation failed — %s", ticker, exc)
                skipped.append(ticker)
                continue

            self._upsert_features(ticker, feat_df)
            self._upsert_labels(ticker, label_df)
            self.db.commit()

            all_features.append(feat_df)
            all_labels.append(label_df)
            processed.append(ticker)
            logger.info("%s: features + labels stored", ticker)

        # ── Build versioned dataset ──────────────────────────────────────
        dataset_version: int | None = None
        dist: dict | None = None

        if build_ds and all_features:
            features_combined = pd.concat(all_features, ignore_index=True)
            labels_combined   = pd.concat(all_labels,   ignore_index=True)

            latest = self.db.query(func.max(DatasetVersion.version)).scalar() or 0
            new_ver = latest + 1

            try:
                meta = build_dataset(
                    features_combined,
                    labels_combined,
                    split_date=split_date,
                    version=new_ver,
                )

                dv = DatasetVersion(
                    version=new_ver,
                    tickers=json.dumps(meta["tickers"]),
                    date_range_start=date.fromisoformat(meta["date_range_start"]),
                    date_range_end=date.fromisoformat(meta["date_range_end"]),
                    n_rows=meta["n_rows"],
                    n_train=meta["n_train"],
                    n_test=meta["n_test"],
                    feature_list=json.dumps(meta["feature_list"]),
                    label_distribution=json.dumps(meta["label_distribution"]),
                    split_date=date.fromisoformat(meta["split_date"]),
                    file_path=meta["file_path"],
                )
                self.db.add(dv)
                self.db.commit()

                dataset_version = new_ver
                dist = meta["label_distribution"]
                logger.info("Dataset v%d created", new_ver)

            except Exception as exc:
                logger.error("Dataset build failed: %s", exc)
                self.db.rollback()

        return PipelineRunResponse(
            message=(
                f"Pipeline complete: {len(processed)} tickers processed, "
                f"{len(skipped)} skipped"
                + (f", dataset v{dataset_version} created" if dataset_version else "")
            ),
            tickers_processed=processed,
            tickers_skipped=skipped,
            dataset_version=dataset_version,
            label_distribution=dist,
        )

    # ------------------------------------------------------------------
    # Feature list (recent N rows for a ticker)
    # ------------------------------------------------------------------

    def get_feature_list(self, ticker: str, limit: int = 30) -> FeatureListResponse:
        rows = (
            self.db.query(FeaturesData)
            .filter(FeaturesData.ticker == ticker.upper())
            .order_by(FeaturesData.date.desc())
            .limit(limit)
            .all()
        )
        rows = list(reversed(rows))   # return chronological order

        result = []
        for r in rows:
            result.append(
                FeatureRow(
                    date=str(r.date),
                    close=_safe(r.close),
                    sma_10=_safe(r.sma_10),   sma_20=_safe(r.sma_20),
                    sma_50=_safe(r.sma_50),   sma_200=_safe(r.sma_200),
                    ema_10=_safe(r.ema_10),   ema_20=_safe(r.ema_20),
                    ema_50=_safe(r.ema_50),
                    macd_line=_safe(r.macd_line),
                    macd_signal=_safe(r.macd_signal),
                    macd_hist=_safe(r.macd_hist),
                    adx_14=_safe(r.adx_14),
                    price_vs_sma20_pct=_safe(r.price_vs_sma20_pct),
                    price_vs_sma50_pct=_safe(r.price_vs_sma50_pct),
                    rsi_14=_safe(r.rsi_14),   stoch_k=_safe(r.stoch_k),
                    stoch_d=_safe(r.stoch_d), roc_10=_safe(r.roc_10),
                    williams_r=_safe(r.williams_r),
                    bb_upper=_safe(r.bb_upper), bb_lower=_safe(r.bb_lower),
                    bb_width=_safe(r.bb_width), bb_pct_b=_safe(r.bb_pct_b),
                    atr_14=_safe(r.atr_14),   hist_vol_20=_safe(r.hist_vol_20),
                    obv=_safe_int(r.obv),
                    vol_sma_20=_safe(r.vol_sma_20),
                    vol_ratio=_safe(r.vol_ratio), cmf_20=_safe(r.cmf_20),
                    daily_return=_safe(r.daily_return),
                    return_3d=_safe(r.return_3d),
                    return_5d=_safe(r.return_5d),
                    return_10d=_safe(r.return_10d),
                    gap_pct=_safe(r.gap_pct),
                    hl_range_pct=_safe(r.hl_range_pct),
                    candle_body_pct=_safe(r.candle_body_pct),
                )
            )
        return FeatureListResponse(ticker=ticker.upper(), count=len(result), rows=result)

    # ------------------------------------------------------------------
    # Feature statistics
    # ------------------------------------------------------------------

    def get_feature_stats(self, ticker: str) -> FeatureStatsResponse:
        rows = (
            self.db.query(FeaturesData)
            .filter(FeaturesData.ticker == ticker.upper())
            .all()
        )
        if not rows:
            return FeatureStatsResponse(ticker=ticker.upper(), total_rows=0, stats={})

        data = {col: [] for col in ALL_FEATURES}
        for r in rows:
            for col in ALL_FEATURES:
                val = getattr(r, col, None)
                data[col].append(float(val) if val is not None else np.nan)

        stats: dict[str, FeatureStat] = {}
        for col in ALL_FEATURES:
            series  = pd.Series(data[col], dtype=float)
            valid   = series.dropna()
            null_ct = series.isna().sum()
            if len(valid) == 0:
                stats[col] = FeatureStat(mean=None, std=None, min=None, max=None, null_pct=100.0)
            else:
                stats[col] = FeatureStat(
                    mean=round(float(valid.mean()), 4),
                    std=round(float(valid.std()),  4),
                    min=round(float(valid.min()),  4),
                    max=round(float(valid.max()),  4),
                    null_pct=round(null_ct / len(series) * 100, 1),
                )
        return FeatureStatsResponse(ticker=ticker.upper(), total_rows=len(rows), stats=stats)

    # ------------------------------------------------------------------
    # Label distribution
    # ------------------------------------------------------------------

    def get_label_distribution(self, ticker: str | None = None) -> list[LabelDistribution]:
        query = self.db.query(
            LabelsData.ticker,
            LabelsData.signal_label,
            func.count().label("cnt"),
        ).filter(LabelsData.signal_label.isnot(None))

        if ticker:
            query = query.filter(LabelsData.ticker == ticker.upper())

        query = query.group_by(LabelsData.ticker, LabelsData.signal_label)
        rows  = query.all()

        # Aggregate per ticker
        agg: dict[str, dict] = {}
        for r in rows:
            t = r.ticker
            if t not in agg:
                agg[t] = {"BUY": 0, "SELL": 0, "HOLD": 0}
            if r.signal_label in agg[t]:
                agg[t][r.signal_label] = int(r.cnt)

        result = []
        for t, counts in sorted(agg.items()):
            total = counts["BUY"] + counts["SELL"] + counts["HOLD"]
            result.append(
                LabelDistribution(
                    ticker=t, total=total,
                    BUY=counts["BUY"], SELL=counts["SELL"], HOLD=counts["HOLD"],
                )
            )
        return result

    # ------------------------------------------------------------------
    # Dataset versions
    # ------------------------------------------------------------------

    def get_dataset_versions(self) -> list[DatasetVersionInfo]:
        versions = (
            self.db.query(DatasetVersion)
            .order_by(DatasetVersion.version.desc())
            .all()
        )
        return [self._version_to_schema(v) for v in versions]

    def get_dataset_summary(self, version: int) -> DatasetVersionInfo | None:
        v = (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.version == version)
            .first()
        )
        return self._version_to_schema(v) if v else None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _upsert_features(self, ticker: str, feat_df: pd.DataFrame) -> None:
        self.db.query(FeaturesData).filter(FeaturesData.ticker == ticker).delete()

        records = []
        for _, row in feat_df.iterrows():
            d: dict = {"ticker": ticker, "date": row["date"]}
            d["close"] = _safe(row.get("close"))
            for col in ALL_FEATURES:
                val = row.get(col)
                if col == "obv":
                    d[col] = _safe_int(val)
                else:
                    d[col] = _safe(val)
            records.append(d)

        if records:
            self.db.execute(insert(FeaturesData), records)

    def _upsert_labels(self, ticker: str, label_df: pd.DataFrame) -> None:
        self.db.query(LabelsData).filter(LabelsData.ticker == ticker).delete()

        records = []
        for _, row in label_df.iterrows():
            ret = row.get("future_return_5d")
            records.append({
                "ticker":           ticker,
                "date":             row["date"],
                "future_return_5d": _safe(ret),
                "signal_label":     row.get("signal_label"),
            })

        if records:
            self.db.execute(insert(LabelsData), records)

    @staticmethod
    def _version_to_schema(v: DatasetVersion) -> DatasetVersionInfo:
        def _load(s: str | None, default):
            if not s:
                return default
            try:
                return json.loads(s)
            except Exception:
                return default

        return DatasetVersionInfo(
            version=v.version,
            tickers=_load(v.tickers, []),
            date_range_start=str(v.date_range_start) if v.date_range_start else None,
            date_range_end=str(v.date_range_end) if v.date_range_end else None,
            n_rows=v.n_rows,
            n_train=v.n_train,
            n_test=v.n_test,
            feature_list=_load(v.feature_list, []),
            label_distribution=_load(v.label_distribution, {}),
            split_date=str(v.split_date) if v.split_date else None,
            file_path=v.file_path,
            created_at=str(v.created_at) if v.created_at else None,
        )
