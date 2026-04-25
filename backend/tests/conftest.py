from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base
from app.models.features import DatasetVersion, FeaturesData, LabelsData
from app.models.market import MarketData
from app.models.monitoring import MonitoringReport, RetrainLog
from app.models.portfolio import Watchlist
from app.models.signals import Signal


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    _seed_database(session)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def monitoring_report_payload(db_session: Session) -> dict:
    today = date.today()
    generated_at = datetime.utcnow().isoformat() + "Z"
    return {
        "id": 1,
        "report_date": today.isoformat(),
        "report_type": "daily",
        "drift_share": 42.0,
        "prediction_drift_detected": True,
        "model_perf_f1": 0.61,
        "alert_level": "WARN",
        "evidently_report_html": "ml/artifacts/monitoring/report.html",
        "created_at": generated_at,
        "details": {
            "metadata": {
                "generated_at": generated_at,
                "report_type": "daily",
                "reference_dataset_version": 1,
                "reference_rows": 120,
                "current_rows": 30,
                "current_window_days": 30,
                "feature_columns": ["rsi_14", "macd_line", "vol_ratio"],
            },
            "data_drift": {
                "drift_share": 42.0,
                "drifted_count": 3,
                "feature_count": 7,
                "summary_text": "3 of 7 features drifted in the latest comparison window.",
                "top_drifted": [
                    {
                        "feature": "rsi_14",
                        "drift_detected": True,
                        "drift_score": 0.82,
                        "p_value": 0.01,
                        "reference_mean": 48.0,
                        "current_mean": 56.0,
                        "reference_std": 8.2,
                        "current_std": 10.1,
                        "reference_count": 120,
                        "current_count": 30,
                        "histogram": [
                            {
                                "bin_start": 10.0,
                                "bin_end": 20.0,
                                "reference_density": 0.1,
                                "current_density": 0.0,
                            }
                        ],
                    }
                ],
            },
            "feature_details": [
                {
                    "feature": "rsi_14",
                    "drift_detected": True,
                    "drift_score": 0.82,
                    "p_value": 0.01,
                    "reference_mean": 48.0,
                    "current_mean": 56.0,
                    "reference_std": 8.2,
                    "current_std": 10.1,
                    "reference_count": 120,
                    "current_count": 30,
                    "histogram": [
                        {
                            "bin_start": 10.0,
                            "bin_end": 20.0,
                            "reference_density": 0.1,
                            "current_density": 0.0,
                        }
                    ],
                },
                {
                    "feature": "macd_line",
                    "drift_detected": False,
                    "drift_score": 0.18,
                    "p_value": 0.32,
                    "reference_mean": 0.4,
                    "current_mean": 0.45,
                    "reference_std": 0.2,
                    "current_std": 0.25,
                    "reference_count": 120,
                    "current_count": 30,
                    "histogram": [
                        {
                            "bin_start": -1.0,
                            "bin_end": 0.0,
                            "reference_density": 0.2,
                            "current_density": 0.25,
                        }
                    ],
                },
            ],
            "prediction_drift": {
                "detected": True,
                "threshold": 0.2,
                "reference_counts": {"BUY": 40, "SELL": 30, "HOLD": 50},
                "current_counts": {"BUY": 20, "SELL": 5, "HOLD": 25},
                "reference_ratios": {"BUY": 0.33, "SELL": 0.25, "HOLD": 0.42},
                "current_ratios": {"BUY": 0.4, "SELL": 0.1, "HOLD": 0.5},
                "ratio_shifts": {"BUY": 0.07, "SELL": 0.15, "HOLD": 0.08},
                "largest_ratio_shift": 0.15,
                "reference_total": 120,
                "current_total": 50,
            },
            "performance": {
                "ground_truth_available": True,
                "window_days": 30,
                "baseline_f1": 0.67,
                "baseline_accuracy": 0.7,
                "baseline_source": "training",
                "last_training_at": generated_at,
                "current_f1": 0.61,
                "current_accuracy": 0.65,
                "degradation_pct": 8.96,
                "degradation_detected": True,
                "sample_size": 50,
                "rolling": [
                    {"date": today.isoformat(), "f1": 0.61, "accuracy": 0.65, "sample_size": 50}
                ],
            },
            "freshness": {
                "checked_at": generated_at,
                "stale_threshold_days": 1,
                "stale_count": 1,
                "ticker_count": 2,
                "tickers": [
                    {
                        "ticker": "AAPL",
                        "last_market_date": today.isoformat(),
                        "last_ingested_at": generated_at,
                        "days_stale": 0,
                        "status": "fresh",
                    },
                    {
                        "ticker": "MSFT",
                        "last_market_date": (today - timedelta(days=2)).isoformat(),
                        "last_ingested_at": generated_at,
                        "days_stale": 2,
                        "status": "stale",
                    },
                ],
            },
            "alerts": [
                {
                    "id": "warn-1",
                    "severity": "WARN",
                    "title": "Data drift",
                    "description": "Feature drift crossed the review threshold.",
                    "timestamp": generated_at,
                }
            ],
        },
    }


@pytest.fixture()
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch, monitoring_report_payload: dict) -> TestClient:
    from app import main as main_module
    from app.services import market_service, monitoring_service, watchlist_service
    from ml.data_pipeline import watchlist as watchlist_module

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def fake_watchlist():
        return [
            {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
            {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
        ]

    monkeypatch.setattr(main_module, "start_scheduler", lambda: None)
    monkeypatch.setattr(main_module, "shutdown_scheduler", lambda: None)
    monkeypatch.setattr(watchlist_module, "load_watchlist", fake_watchlist)
    monkeypatch.setattr(watchlist_module, "get_tickers", lambda: ["AAPL", "MSFT"])
    monkeypatch.setattr(market_service, "_WATCHLIST_CACHE", None)
    monkeypatch.setattr(monitoring_service, "_ensure_latest_report", lambda: monitoring_report_payload)
    monkeypatch.setattr(watchlist_service, "_run_watchlist_pipeline", lambda ticker: None)

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def _seed_database(session: Session) -> None:
    today = date.today()
    market_dates = [today - timedelta(days=12 - idx) for idx in range(12)]

    session.add_all(
        [
            Watchlist(ticker="AAPL", company_name="Apple Inc.", sector="Technology", is_active=True),
            Watchlist(ticker="MSFT", company_name="Microsoft Corp.", sector="Technology", is_active=True),
        ]
    )

    for idx, market_date in enumerate(market_dates):
        session.add(
            MarketData(
                ticker="AAPL",
                date=market_date,
                open=100 + idx,
                high=101 + idx,
                low=99 + idx,
                close=100.5 + idx,
                adj_close=100.5 + idx,
                volume=1_000_000 + idx * 100,
            )
        )
        session.add(
            MarketData(
                ticker="MSFT",
                date=market_date,
                open=200 + idx,
                high=201 + idx,
                low=199 + idx,
                close=200.5 + idx,
                adj_close=200.5 + idx,
                volume=2_000_000 + idx * 100,
            )
        )

    session.add_all(
        [
            Signal(
                ticker="AAPL",
                signal_date=market_dates[1],
                signal="BUY",
                confidence=0.82,
                prob_buy=0.82,
                prob_sell=0.08,
                prob_hold=0.10,
                model_version="7",
                model_run_id="run-aapl-buy",
            ),
            Signal(
                ticker="AAPL",
                signal_date=market_dates[5],
                signal="SELL",
                confidence=0.77,
                prob_buy=0.10,
                prob_sell=0.77,
                prob_hold=0.13,
                model_version="7",
                model_run_id="run-aapl-sell",
            ),
            Signal(
                ticker="MSFT",
                signal_date=market_dates[2],
                signal="BUY",
                confidence=0.81,
                prob_buy=0.81,
                prob_sell=0.09,
                prob_hold=0.10,
                model_version="7",
                model_run_id="run-msft-buy",
            ),
            Signal(
                ticker="MSFT",
                signal_date=market_dates[8],
                signal="HOLD",
                confidence=0.63,
                prob_buy=0.15,
                prob_sell=0.22,
                prob_hold=0.63,
                model_version="7",
                model_run_id="run-msft-hold",
            ),
        ]
    )

    for idx, market_date in enumerate(market_dates[-5:]):
        session.add(
            FeaturesData(
                ticker="AAPL",
                date=market_date,
                close=110 + idx,
                sma_10=109 + idx,
                sma_20=108 + idx,
                ema_10=109.5 + idx,
                ema_20=108.5 + idx,
                macd_line=0.5 + idx * 0.1,
                macd_signal=0.3 + idx * 0.1,
                macd_hist=0.2,
                rsi_14=55 + idx,
                bb_width=4.2,
                atr_14=2.1,
                vol_ratio=1.1,
                daily_return=0.6,
                return_5d=2.2,
            )
        )
        session.add(
            LabelsData(
                ticker="AAPL",
                date=market_date,
                future_return_5d=0.03 if idx % 2 == 0 else -0.01,
                signal_label="BUY" if idx % 2 == 0 else "HOLD",
            )
        )
        session.add(
            LabelsData(
                ticker="MSFT",
                date=market_date,
                future_return_5d=-0.04 if idx == 2 else 0.01,
                signal_label="SELL" if idx == 2 else "HOLD",
            )
        )

    session.add(
        DatasetVersion(
            version=1,
            tickers='["AAPL","MSFT"]',
            date_range_start=market_dates[0],
            date_range_end=market_dates[-1],
            n_rows=10,
            n_train=8,
            n_test=2,
            feature_list='["sma_10","rsi_14","macd_line"]',
            label_distribution='{"BUY":3,"SELL":1,"HOLD":6}',
            split_date=market_dates[8],
            file_path="ml/artifacts/datasets/dataset_v1.parquet",
        )
    )

    session.add_all(
        [
            MonitoringReport(
                report_date=today - timedelta(days=1),
                report_type="daily",
                drift_share=18.0,
                drifted_features_json="[]",
                prediction_drift_detected=False,
                model_perf_f1=0.66,
                alert_level="INFO",
                evidently_report_html="report-old.html",
            ),
            MonitoringReport(
                report_date=today,
                report_type="daily",
                drift_share=42.0,
                drifted_features_json='["rsi_14"]',
                prediction_drift_detected=True,
                model_perf_f1=0.61,
                alert_level="WARN",
                evidently_report_html="report.html",
            ),
            RetrainLog(
                triggered_at=datetime.utcnow() - timedelta(days=2),
                trigger_reason="Manual retrain",
                old_model_version="6",
                new_model_version="7",
                new_f1=0.67,
                promoted=True,
                notes="Improved on validation",
            ),
        ]
    )

    session.commit()
