"""Monitoring and drift detection utilities for AlgoTrade Sentinel."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import accuracy_score, f1_score
from sqlalchemy import text

from ml.data_pipeline.database import SessionLocal, engine
from ml.data_pipeline.watchlist import get_tickers
from ml.features.feature_engineer import ALL_FEATURES
from ml.registry import registry_manager
from ml.training.mlflow_logger import EXPERIMENT_NAME, get_default_uri

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[2]
_DATASETS_DIR = _PROJECT_ROOT / "ml" / "artifacts" / "datasets"
_MONITORING_DIR = _PROJECT_ROOT / "ml" / "artifacts" / "monitoring"
_MONITORING_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class MonitoringConfig:
    current_window_days: int = 30
    drift_p_value_threshold: float = 0.05
    drift_share_warn_threshold: float = 15.0
    drift_share_critical_threshold: float = 30.0
    prediction_shift_threshold: float = 0.20
    performance_warn_drop_pct: float = 5.0
    performance_critical_drop_pct: float = 10.0
    freshness_stale_days: int = 1
    top_drift_count: int = 10


def generate_monitoring_report(
    report_date: date | None = None,
    report_type: str = "daily",
    config: MonitoringConfig | None = None,
) -> dict[str, Any]:
    """Generate a full monitoring report without persisting it."""
    cfg = config or MonitoringConfig()
    report_date = report_date or date.today()

    reference_df, dataset_meta = _load_reference_dataset()
    feature_columns = dataset_meta.get("feature_list") or [c for c in ALL_FEATURES if c in reference_df.columns]
    current_df, current_as_of = _load_current_feature_window(
        window_days=cfg.current_window_days,
        feature_columns=feature_columns,
    )

    feature_details = _compute_feature_drift_details(
        reference_df=reference_df,
        current_df=current_df,
        feature_columns=feature_columns,
        p_threshold=cfg.drift_p_value_threshold,
    )
    drifted_count = sum(1 for item in feature_details if item["drift_detected"])
    feature_count = len(feature_columns)
    drift_share = round((drifted_count / feature_count) * 100, 2) if feature_count else 0.0
    top_drifted = sorted(feature_details, key=lambda item: item["drift_score"], reverse=True)[: cfg.top_drift_count]

    prediction_drift = _compute_prediction_drift(
        reference_df=reference_df,
        window_days=cfg.current_window_days,
        threshold=cfg.prediction_shift_threshold,
    )
    performance = _compute_model_performance(window_days=cfg.current_window_days)
    freshness = _compute_data_freshness(report_date=report_date, stale_days=cfg.freshness_stale_days)

    alerts = _build_alerts(
        drift_share=drift_share,
        drifted_count=drifted_count,
        feature_count=feature_count,
        prediction_drift=prediction_drift,
        performance=performance,
        freshness=freshness,
        cfg=cfg,
    )
    alert_level = _overall_alert_level(alerts)
    html_path = _save_evidently_html(
        reference_df=reference_df,
        current_df=current_df,
        feature_columns=feature_columns,
        report_date=report_date,
        report_type=report_type,
        summary={
            "drift_share": drift_share,
            "drifted_count": drifted_count,
            "feature_count": feature_count,
            "prediction_drift_detected": prediction_drift["detected"],
            "alert_level": alert_level,
        },
    )

    details = {
        "metadata": {
            "generated_at": _utcnow().isoformat(),
            "report_type": report_type,
            "reference_dataset_version": dataset_meta.get("version"),
            "reference_dataset_path": dataset_meta.get("file_path"),
            "reference_rows": int(len(reference_df)),
            "current_rows": int(len(current_df)),
            "current_window_days": cfg.current_window_days,
            "feature_columns": feature_columns,
            "current_as_of_date": current_as_of.isoformat() if current_as_of else None,
            "drift_p_value_threshold": cfg.drift_p_value_threshold,
            "prediction_shift_threshold": cfg.prediction_shift_threshold,
        },
        "data_drift": {
            "drift_share": drift_share,
            "drifted_count": drifted_count,
            "feature_count": feature_count,
            "summary_text": f"{drifted_count} of {feature_count} features drifted" if feature_count else "No features available",
            "top_drifted": top_drifted,
        },
        "feature_details": feature_details,
        "prediction_drift": prediction_drift,
        "performance": performance,
        "freshness": freshness,
        "alerts": alerts,
    }

    return {
        "report_date": report_date,
        "report_type": report_type,
        "drift_share": drift_share,
        "prediction_drift_detected": bool(prediction_drift["detected"]),
        "model_perf_f1": performance.get("current_f1"),
        "alert_level": alert_level,
        "evidently_report_html": str(html_path),
        "details": details,
    }


def generate_and_save_monitoring_report(
    report_date: date | None = None,
    report_type: str = "daily",
    config: MonitoringConfig | None = None,
) -> dict[str, Any]:
    """Generate and persist a monitoring report."""
    report = generate_monitoring_report(report_date=report_date, report_type=report_type, config=config)
    report_id = save_monitoring_report(report)
    report["id"] = report_id
    return report


def save_monitoring_report(report: dict[str, Any]) -> int:
    """Persist a monitoring report and return the created id."""
    payload = json.dumps(report["details"], default=_json_default)
    with SessionLocal() as session:
        result = session.execute(
            text(
                """
                INSERT INTO monitoring_reports (
                    report_date,
                    report_type,
                    drift_share,
                    drifted_features_json,
                    prediction_drift_detected,
                    model_perf_f1,
                    alert_level,
                    evidently_report_html
                )
                VALUES (
                    :report_date,
                    :report_type,
                    :drift_share,
                    :drifted_features_json,
                    :prediction_drift_detected,
                    :model_perf_f1,
                    :alert_level,
                    :evidently_report_html
                )
                """
            ),
            {
                "report_date": report["report_date"],
                "report_type": report["report_type"],
                "drift_share": report["drift_share"],
                "drifted_features_json": payload,
                "prediction_drift_detected": int(report["prediction_drift_detected"]),
                "model_perf_f1": report["model_perf_f1"],
                "alert_level": report["alert_level"],
                "evidently_report_html": report["evidently_report_html"],
            },
        )
        session.commit()
        return int(result.lastrowid)


def get_latest_saved_report() -> dict[str, Any] | None:
    with SessionLocal() as session:
        row = session.execute(
            text(
                """
                SELECT *
                FROM monitoring_reports
                ORDER BY report_date DESC, created_at DESC, id DESC
                LIMIT 1
                """
            )
        ).mappings().first()

    return _deserialize_report_row(row) if row else None


def report_is_stale(report: dict[str, Any] | None, report_date: date | None = None) -> bool:
    if report is None:
        return True
    target_date = report_date or date.today()
    return report.get("report_date") != target_date


def _load_reference_dataset() -> tuple[pd.DataFrame, dict[str, Any]]:
    meta_row = _get_latest_dataset_row()
    if meta_row:
        file_path = Path(meta_row["file_path"]) if meta_row.get("file_path") else None
        if file_path and not file_path.is_absolute():
            file_path = (_PROJECT_ROOT / file_path).resolve()
        feature_list = _parse_json(meta_row.get("feature_list"), [])
        meta = {
            "version": meta_row.get("version"),
            "file_path": str(file_path) if file_path else None,
            "feature_list": feature_list,
            "split_date": str(meta_row.get("split_date")) if meta_row.get("split_date") else None,
        }
    else:
        meta = _load_latest_dataset_meta_file()
        file_path = Path(meta["file_path"])

    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"Reference dataset not found at {file_path}")

    reference_df = pd.read_parquet(file_path)
    if "date" in reference_df.columns:
        reference_df["date"] = pd.to_datetime(reference_df["date"])
    return reference_df, meta


def _load_current_feature_window(
    window_days: int,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, date | None]:
    if not feature_columns:
        return pd.DataFrame(columns=["ticker", "date"]), None
    with SessionLocal() as session:
        as_of_date = session.execute(text("SELECT MAX(date) FROM features_data")).scalar()
    as_of_date = _coerce_date(as_of_date)
    if as_of_date is None:
        return pd.DataFrame(columns=["ticker", "date", *feature_columns]), None

    start_date = as_of_date - timedelta(days=max(window_days - 1, 0))
    sql = text(
        f"""
        SELECT ticker, date, {", ".join(feature_columns)}
        FROM features_data
        WHERE date >= :start_date
        ORDER BY date ASC, ticker ASC
        """
    )
    current_df = pd.read_sql(sql, engine, params={"start_date": start_date})
    if not current_df.empty:
        current_df["date"] = pd.to_datetime(current_df["date"])
    return current_df, as_of_date


def _compute_feature_drift_details(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    feature_columns: list[str],
    p_threshold: float,
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for feature in feature_columns:
        ref = pd.to_numeric(reference_df.get(feature), errors="coerce").dropna()
        cur = pd.to_numeric(current_df.get(feature), errors="coerce").dropna()

        if ref.empty or cur.empty:
            details.append(
                {
                    "feature": feature,
                    "drift_detected": False,
                    "drift_score": 0.0,
                    "p_value": None,
                    "reference_mean": _safe_round(ref.mean()),
                    "current_mean": _safe_round(cur.mean()),
                    "reference_std": _safe_round(ref.std(ddof=0)),
                    "current_std": _safe_round(cur.std(ddof=0)),
                    "reference_count": int(ref.shape[0]),
                    "current_count": int(cur.shape[0]),
                    "histogram": [],
                }
            )
            continue

        ks_result = ks_2samp(ref, cur, alternative="two-sided", method="auto")
        histogram = _build_histogram(ref.to_numpy(), cur.to_numpy())
        details.append(
            {
                "feature": feature,
                "drift_detected": bool(ks_result.pvalue < p_threshold),
                "drift_score": round(float(ks_result.statistic), 6),
                "p_value": round(float(ks_result.pvalue), 6),
                "reference_mean": _safe_round(ref.mean()),
                "current_mean": _safe_round(cur.mean()),
                "reference_std": _safe_round(ref.std(ddof=0)),
                "current_std": _safe_round(cur.std(ddof=0)),
                "reference_count": int(ref.shape[0]),
                "current_count": int(cur.shape[0]),
                "histogram": histogram,
            }
        )
    return details


def _compute_prediction_drift(
    reference_df: pd.DataFrame,
    window_days: int,
    threshold: float,
) -> dict[str, Any]:
    labels = ["BUY", "SELL", "HOLD"]
    reference_counts = (
        reference_df["signal_label"].value_counts().reindex(labels, fill_value=0).to_dict()
        if "signal_label" in reference_df.columns
        else {label: 0 for label in labels}
    )

    with SessionLocal() as session:
        as_of_date = session.execute(text("SELECT MAX(signal_date) FROM signals")).scalar()
    as_of_date = _coerce_date(as_of_date)
    if as_of_date is None:
        current_counts = {label: 0 for label in labels}
    else:
        start_date = as_of_date - timedelta(days=max(window_days - 1, 0))
        current_df = pd.read_sql(
            text(
                """
                SELECT signal
                FROM signals
                WHERE signal_date >= :start_date
                """
            ),
            engine,
            params={"start_date": start_date},
        )
        current_counts = current_df["signal"].value_counts().reindex(labels, fill_value=0).to_dict()

    ref_total = int(sum(reference_counts.values()))
    cur_total = int(sum(current_counts.values()))
    reference_ratios = _distribution_ratios(reference_counts)
    current_ratios = _distribution_ratios(current_counts)
    shifts = {
        label: round(abs(current_ratios[label] - reference_ratios[label]), 4)
        for label in labels
    }
    largest_shift = max(shifts.values()) if shifts else 0.0

    return {
        "detected": bool(cur_total > 0 and largest_shift > threshold),
        "threshold": threshold,
        "reference_counts": reference_counts,
        "current_counts": current_counts,
        "reference_ratios": reference_ratios,
        "current_ratios": current_ratios,
        "ratio_shifts": shifts,
        "largest_ratio_shift": round(largest_shift, 4),
        "reference_total": ref_total,
        "current_total": cur_total,
    }


def _compute_model_performance(window_days: int) -> dict[str, Any]:
    baseline = _get_baseline_metrics()
    joined = pd.read_sql(
        text(
            """
            SELECT s.signal_date, s.signal, l.signal_label
            FROM signals s
            INNER JOIN labels_data l
                ON l.ticker = s.ticker
               AND l.date = s.signal_date
            WHERE l.signal_label IS NOT NULL
            ORDER BY s.signal_date ASC
            """
        ),
        engine,
    )

    if joined.empty:
        return {
            "ground_truth_available": False,
            "window_days": window_days,
            "baseline_f1": baseline.get("baseline_f1"),
            "baseline_accuracy": baseline.get("baseline_accuracy"),
            "baseline_source": baseline.get("baseline_source"),
            "last_training_at": baseline.get("last_training_at"),
            "current_f1": None,
            "current_accuracy": None,
            "degradation_pct": None,
            "degradation_detected": False,
            "sample_size": 0,
            "rolling": [],
        }

    joined["signal_date"] = pd.to_datetime(joined["signal_date"])
    as_of_timestamp = joined["signal_date"].max()
    start_timestamp = as_of_timestamp - pd.Timedelta(days=max(window_days - 1, 0))
    current_window = joined[joined["signal_date"] >= start_timestamp].copy()

    current_accuracy = float(accuracy_score(current_window["signal_label"], current_window["signal"]))
    current_f1 = float(f1_score(current_window["signal_label"], current_window["signal"], average="macro", zero_division=0))
    baseline_f1 = baseline.get("baseline_f1")
    degradation_pct = None
    degradation_detected = False
    if baseline_f1 not in (None, 0):
        degradation_pct = round(((baseline_f1 - current_f1) / baseline_f1) * 100, 2)
        degradation_detected = degradation_pct > 5.0

    rolling = []
    for day in sorted(current_window["signal_date"].dt.normalize().unique()):
        window_start = day - pd.Timedelta(days=max(window_days - 1, 0))
        day_window = joined[(joined["signal_date"] >= window_start) & (joined["signal_date"] <= day)]
        if day_window.empty:
            continue
        rolling.append(
            {
                "date": pd.Timestamp(day).date().isoformat(),
                "f1": round(float(f1_score(day_window["signal_label"], day_window["signal"], average="macro", zero_division=0)), 4),
                "accuracy": round(float(accuracy_score(day_window["signal_label"], day_window["signal"])), 4),
                "sample_size": int(len(day_window)),
            }
        )

    return {
        "ground_truth_available": True,
        "window_days": window_days,
        "baseline_f1": baseline_f1,
        "baseline_accuracy": baseline.get("baseline_accuracy"),
        "baseline_source": baseline.get("baseline_source"),
        "last_training_at": baseline.get("last_training_at"),
        "current_f1": round(current_f1, 4),
        "current_accuracy": round(current_accuracy, 4),
        "degradation_pct": degradation_pct,
        "degradation_detected": degradation_detected,
        "sample_size": int(len(current_window)),
        "rolling": rolling,
    }


def _compute_data_freshness(report_date: date, stale_days: int) -> dict[str, Any]:
    tickers = get_tickers()
    freshness_rows = pd.read_sql(
        text(
            """
            SELECT ticker, MAX(date) AS last_market_date, MAX(created_at) AS last_ingested_at
            FROM market_data
            GROUP BY ticker
            """
        ),
        engine,
    )
    latest_map = {row["ticker"]: row for _, row in freshness_rows.iterrows()}

    ticker_statuses = []
    stale_count = 0
    for ticker in tickers:
        row = latest_map.get(ticker)
        last_market_date = pd.to_datetime(row["last_market_date"]).date() if row is not None and pd.notna(row["last_market_date"]) else None
        last_ingested_at = (
            pd.to_datetime(row["last_ingested_at"]).to_pydatetime().replace(tzinfo=timezone.utc).isoformat()
            if row is not None and pd.notna(row["last_ingested_at"])
            else None
        )
        days_stale = (report_date - last_market_date).days if last_market_date else None
        is_stale = last_market_date is None or days_stale > stale_days
        stale_count += int(is_stale)
        ticker_statuses.append(
            {
                "ticker": ticker,
                "last_market_date": last_market_date.isoformat() if last_market_date else None,
                "last_ingested_at": last_ingested_at,
                "days_stale": days_stale,
                "status": "stale" if is_stale else "fresh",
            }
        )

    return {
        "checked_at": _utcnow().isoformat(),
        "stale_threshold_days": stale_days,
        "stale_count": stale_count,
        "ticker_count": len(ticker_statuses),
        "tickers": ticker_statuses,
    }


def _build_alerts(
    drift_share: float,
    drifted_count: int,
    feature_count: int,
    prediction_drift: dict[str, Any],
    performance: dict[str, Any],
    freshness: dict[str, Any],
    cfg: MonitoringConfig,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    now = _utcnow().isoformat()

    if drift_share >= cfg.drift_share_critical_threshold:
        alerts.append(
            _alert(
                alert_id="critical-drift",
                severity="CRITICAL",
                title="Critical feature drift detected",
                description=f"{drifted_count} of {feature_count} features drifted ({drift_share:.2f}%).",
                timestamp=now,
            )
        )
    elif drift_share >= cfg.drift_share_warn_threshold:
        alerts.append(
            _alert(
                alert_id="warn-drift",
                severity="WARN",
                title="Feature drift rising",
                description=f"{drifted_count} of {feature_count} features drifted ({drift_share:.2f}%).",
                timestamp=now,
            )
        )

    if prediction_drift["detected"]:
        alerts.append(
            _alert(
                alert_id="prediction-drift",
                severity="WARN",
                title="Prediction mix shifted",
                description=f"BUY/SELL/HOLD ratio changed by up to {prediction_drift['largest_ratio_shift'] * 100:.1f}%.",
                timestamp=now,
            )
        )

    degradation_pct = performance.get("degradation_pct")
    if degradation_pct is not None:
        if degradation_pct > cfg.performance_critical_drop_pct:
            alerts.append(
                _alert(
                    alert_id="performance-critical",
                    severity="CRITICAL",
                    title="Model performance degraded",
                    description=f"Current F1 dropped {degradation_pct:.2f}% from baseline.",
                    timestamp=now,
                )
            )
        elif degradation_pct > cfg.performance_warn_drop_pct:
            alerts.append(
                _alert(
                    alert_id="performance-warn",
                    severity="WARN",
                    title="Model performance slipping",
                    description=f"Current F1 dropped {degradation_pct:.2f}% from baseline.",
                    timestamp=now,
                )
            )

    if freshness["stale_count"] > 0:
        severity = "CRITICAL" if freshness["stale_count"] == freshness["ticker_count"] else "WARN"
        alerts.append(
            _alert(
                alert_id="stale-data",
                severity=severity,
                title="Data freshness issue",
                description=f"{freshness['stale_count']} ticker(s) have market data older than {cfg.freshness_stale_days} day(s).",
                timestamp=now,
            )
        )

    if not alerts:
        alerts.append(
            _alert(
                alert_id="healthy",
                severity="INFO",
                title="Monitoring healthy",
                description="No active drift, performance, or freshness alerts.",
                timestamp=now,
            )
        )
    return alerts


def _save_evidently_html(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    feature_columns: list[str],
    report_date: date,
    report_type: str,
    summary: dict[str, Any],
) -> Path:
    output_path = _MONITORING_DIR / f"{report_type}_{report_date.isoformat()}_{datetime.now().strftime('%H%M%S')}.html"
    try:
        report = _build_evidently_report()
        if report is not None and not reference_df.empty and not current_df.empty and feature_columns:
            report.run(
                reference_data=reference_df[feature_columns].copy(),
                current_data=current_df[feature_columns].copy(),
            )
            report.save_html(str(output_path))
            return output_path
    except Exception as exc:
        logger.warning("Evidently report generation failed, using fallback HTML: %s", exc)

    output_path.write_text(_fallback_html(summary), encoding="utf-8")
    return output_path


def _build_evidently_report():
    try:
        try:
            from evidently import Report
        except ImportError:
            from evidently.report import Report

        try:
            from evidently.presets import DataDriftPreset
        except ImportError:
            from evidently.metric_preset import DataDriftPreset

        return Report(metrics=[DataDriftPreset()])
    except Exception:
        return None


def _get_baseline_metrics() -> dict[str, Any]:
    try:
        champion = registry_manager.get_champion()
        if champion:
            return {
                "baseline_f1": _safe_round(champion.get("f1_macro"), 4),
                "baseline_accuracy": _safe_round(champion.get("accuracy"), 4),
                "baseline_source": "champion",
                "last_training_at": _mlflow_latest_training_timestamp(),
            }
    except Exception:
        champion = None

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        mlflow.set_tracking_uri(get_default_uri())
        client = MlflowClient()
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment is None:
            raise ValueError("No experiment found")
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.f1_macro DESC", "start_time DESC"],
            max_results=1,
        )
        if not runs:
            raise ValueError("No runs found")
        run = runs[0]
        return {
            "baseline_f1": _safe_round(run.data.metrics.get("f1_macro"), 4),
            "baseline_accuracy": _safe_round(run.data.metrics.get("accuracy"), 4),
            "baseline_source": "best_training_run",
            "last_training_at": _ms_to_iso(run.info.start_time),
        }
    except Exception:
        return {
            "baseline_f1": None,
            "baseline_accuracy": None,
            "baseline_source": "unavailable",
            "last_training_at": None,
        }


def _mlflow_latest_training_timestamp() -> str | None:
    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        mlflow.set_tracking_uri(get_default_uri())
        client = MlflowClient()
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment is None:
            return None
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1,
        )
        if not runs:
            return None
        return _ms_to_iso(runs[0].info.start_time)
    except Exception:
        return None


def _get_latest_dataset_row() -> dict[str, Any] | None:
    with SessionLocal() as session:
        row = session.execute(
            text(
                """
                SELECT version, file_path, feature_list, split_date
                FROM dataset_versions
                ORDER BY version DESC
                LIMIT 1
                """
            )
        ).mappings().first()
    return dict(row) if row else None


def _load_latest_dataset_meta_file() -> dict[str, Any]:
    meta_files = sorted(_DATASETS_DIR.glob("dataset_v*_meta.json"))
    if not meta_files:
        raise FileNotFoundError("No dataset metadata files found in ml/artifacts/datasets")
    meta = json.loads(meta_files[-1].read_text(encoding="utf-8"))
    return meta


def _build_histogram(reference: np.ndarray, current: np.ndarray, bins: int = 12) -> list[dict[str, float]]:
    finite_reference = reference[np.isfinite(reference)]
    finite_current = current[np.isfinite(current)]
    combined = np.concatenate([finite_reference, finite_current])
    if combined.size == 0:
        return []
    if np.nanmin(combined) == np.nanmax(combined):
        value = float(np.nanmin(combined))
        return [
            {
                "bin_start": round(value, 6),
                "bin_end": round(value, 6),
                "reference_density": 1.0,
                "current_density": 1.0,
            }
        ]

    edges = np.histogram_bin_edges(combined, bins=bins)
    ref_hist, _ = np.histogram(finite_reference, bins=edges, density=True)
    cur_hist, _ = np.histogram(finite_current, bins=edges, density=True)
    return [
        {
            "bin_start": round(float(edges[idx]), 6),
            "bin_end": round(float(edges[idx + 1]), 6),
            "reference_density": round(float(ref_hist[idx]), 6),
            "current_density": round(float(cur_hist[idx]), 6),
        }
        for idx in range(len(edges) - 1)
    ]


def _distribution_ratios(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    if total <= 0:
        return {key: 0.0 for key in counts}
    return {key: round(value / total, 4) for key, value in counts.items()}


def _deserialize_report_row(row: dict[str, Any]) -> dict[str, Any]:
    details = _parse_json(row.get("drifted_features_json"), {})
    return {
        "id": row.get("id"),
        "report_date": _coerce_date(row.get("report_date")),
        "report_type": row.get("report_type"),
        "drift_share": row.get("drift_share"),
        "prediction_drift_detected": bool(row.get("prediction_drift_detected")),
        "model_perf_f1": row.get("model_perf_f1"),
        "alert_level": row.get("alert_level"),
        "evidently_report_html": row.get("evidently_report_html"),
        "details": details,
        "created_at": _coerce_datetime(row.get("created_at")),
    }


def _alert(
    alert_id: str,
    severity: str,
    title: str,
    description: str,
    timestamp: str,
) -> dict[str, Any]:
    return {
        "id": alert_id,
        "severity": severity,
        "title": title,
        "description": description,
        "timestamp": timestamp,
    }


def _overall_alert_level(alerts: list[dict[str, Any]]) -> str:
    priorities = {"INFO": 0, "WARN": 1, "CRITICAL": 2}
    return max(alerts, key=lambda item: priorities.get(item["severity"], 0))["severity"]


def _fallback_html(summary: dict[str, Any]) -> str:
    return f"""
    <html>
      <head>
        <title>AlgoTrade Sentinel Monitoring Report</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; background: #0f172a; color: #e2e8f0; }}
          .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
          .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
          .value {{ font-size: 28px; font-weight: 700; margin-top: 6px; }}
        </style>
      </head>
      <body>
        <h1>AlgoTrade Sentinel Monitoring Report</h1>
        <div class="card">
          <div class="label">Drift Share</div>
          <div class="value">{summary['drift_share']}%</div>
        </div>
        <div class="card">
          <div class="label">Drifted Features</div>
          <div class="value">{summary['drifted_count']} / {summary['feature_count']}</div>
        </div>
        <div class="card">
          <div class="label">Prediction Drift</div>
          <div class="value">{'Detected' if summary['prediction_drift_detected'] else 'Not detected'}</div>
        </div>
        <div class="card">
          <div class="label">Alert Level</div>
          <div class="value">{summary['alert_level']}</div>
        </div>
      </body>
    </html>
    """.strip()


def _safe_round(value: Any, digits: int = 6) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _parse_json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _ms_to_iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _coerce_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _coerce_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None
