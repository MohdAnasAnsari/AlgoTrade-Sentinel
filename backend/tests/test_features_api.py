from __future__ import annotations


def test_feature_list_returns_recent_rows(client) -> None:
    response = client.get("/api/features/list/AAPL?limit=3")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["count"] == 3


def test_feature_stats_returns_named_feature_metrics(client) -> None:
    response = client.get("/api/features/stats/AAPL")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] >= 1
    assert "rsi_14" in payload["stats"]
    assert payload["stats"]["rsi_14"]["mean"] is not None


def test_label_distribution_returns_all_tickers(client) -> None:
    response = client.get("/api/labels/distribution")
    assert response.status_code == 200
    payload = response.json()
    tickers = {item["ticker"] for item in payload}
    assert {"AAPL", "MSFT"}.issubset(tickers)


def test_label_distribution_for_single_ticker_returns_counts(client) -> None:
    response = client.get("/api/labels/distribution/AAPL")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["total"] > 0


def test_dataset_versions_returns_seeded_dataset(client) -> None:
    response = client.get("/api/dataset/versions")
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["version"] == 1


def test_dataset_summary_returns_requested_version(client) -> None:
    response = client.get("/api/dataset/1/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == 1
    assert payload["tickers"] == ["AAPL", "MSFT"]
