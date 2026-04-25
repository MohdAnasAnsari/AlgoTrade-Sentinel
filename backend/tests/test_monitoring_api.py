from __future__ import annotations


def test_monitoring_latest_returns_summary(client) -> None:
    response = client.get("/api/monitoring/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_level"] == "WARN"
    assert payload["drift_share"] == 42.0


def test_monitoring_history_returns_db_rows(client) -> None:
    response = client.get("/api/monitoring/history?days=5")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2


def test_monitoring_data_drift_returns_summary(client) -> None:
    response = client.get("/api/monitoring/drift/data")
    assert response.status_code == 200
    payload = response.json()
    assert payload["drifted_count"] == 3
    assert payload["top_drifted"][0]["feature"] == "rsi_14"


def test_monitoring_feature_drift_returns_sorted_rows(client) -> None:
    response = client.get("/api/monitoring/drift/features")
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["feature"] == "rsi_14"
    assert payload[0]["drift_score"] >= payload[-1]["drift_score"]


def test_monitoring_prediction_drift_returns_distribution_shift(client) -> None:
    response = client.get("/api/monitoring/drift/predictions")
    assert response.status_code == 200
    payload = response.json()
    assert payload["detected"] is True
    assert payload["reference_total"] == 120


def test_monitoring_performance_returns_rolling_metrics(client) -> None:
    response = client.get("/api/monitoring/performance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["degradation_detected"] is True
    assert len(payload["rolling"]) == 1


def test_monitoring_freshness_returns_ticker_statuses(client) -> None:
    response = client.get("/api/monitoring/freshness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker_count"] == 2
    assert payload["tickers"][1]["status"] == "stale"


def test_monitoring_alerts_returns_active_alerts(client) -> None:
    response = client.get("/api/monitoring/alerts")
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["severity"] == "WARN"


def test_monitoring_retrain_history_returns_log_entries(client) -> None:
    response = client.get("/api/monitoring/retrain/history?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["new_model_version"] == "7"
