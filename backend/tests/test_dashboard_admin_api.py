from __future__ import annotations


def test_dashboard_overview_returns_home_payload(client) -> None:
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio"]["total_value"] > 0
    assert len(payload["pipeline_status"]) == 4


def test_alerts_api_returns_generated_alerts(client) -> None:
    response = client.get("/api/alerts/?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1


def test_watchlist_add_and_remove_work(client) -> None:
    add_response = client.post("/api/watchlist/add", json={"ticker": "NVDA", "company_name": "NVIDIA Corp."})
    assert add_response.status_code == 200
    assert add_response.json()["success"] is True

    remove_response = client.delete("/api/watchlist/NVDA")
    assert remove_response.status_code == 200
    assert remove_response.json()["success"] is True


def test_settings_get_returns_sections(client) -> None:
    response = client.get("/api/settings")
    assert response.status_code == 200
    payload = response.json()
    assert "model" in payload
    assert "portfolio" in payload


def test_settings_save_persists_updates(client) -> None:
    response = client.post("/api/settings", json={"portfolio": {"initial_cash": 125000, "max_positions": 4, "transaction_cost": 0.002}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio"]["initial_cash"] == 125000
    assert payload["portfolio"]["max_positions"] == 4
