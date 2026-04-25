from __future__ import annotations


def test_portfolio_summary_returns_rebuilt_snapshot(client) -> None:
    response = client.get("/api/portfolio/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_value"] > 0
    assert payload["open_positions"] >= 1


def test_portfolio_positions_returns_open_positions(client) -> None:
    response = client.get("/api/portfolio/positions")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert all(item["status"] == "OPEN" for item in payload)


def test_portfolio_position_detail_returns_orders(client) -> None:
    response = client.get("/api/portfolio/positions/MSFT")
    assert response.status_code == 200
    payload = response.json()
    assert payload["position"]["ticker"] == "MSFT"
    assert len(payload["orders"]) >= 1


def test_portfolio_orders_returns_trade_log(client) -> None:
    response = client.get("/api/portfolio/orders?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 3
    assert any(item["order_type"] == "SELL" for item in payload["items"])


def test_portfolio_history_returns_time_series(client) -> None:
    response = client.get("/api/portfolio/history?days=5")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert payload[-1]["total_value"] > 0


def test_portfolio_pnl_returns_breakdown(client) -> None:
    response = client.get("/api/portfolio/pnl")
    assert response.status_code == 200
    payload = response.json()
    assert "realized_pnl" in payload
    assert "unrealized_pnl" in payload
