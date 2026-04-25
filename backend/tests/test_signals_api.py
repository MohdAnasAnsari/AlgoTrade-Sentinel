from __future__ import annotations


def test_signals_latest_returns_most_recent_per_ticker(client) -> None:
    response = client.get("/api/signals/latest")
    assert response.status_code == 200
    payload = response.json()
    assert {item["ticker"] for item in payload} == {"AAPL", "MSFT"}


def test_signals_latest_filter_returns_matching_signal(client) -> None:
    response = client.get("/api/signals/latest?signal=SELL")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["ticker"] == "AAPL"
    assert payload[0]["signal"] == "SELL"


def test_signal_history_returns_joined_price_points(client) -> None:
    response = client.get("/api/signals/history/AAPL?limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 2
    assert payload[0]["close"] is not None


def test_signal_by_id_returns_signal_record(client) -> None:
    response = client.get("/api/signals/1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["signal"] == "BUY"


def test_ticker_latest_signal_returns_row(client) -> None:
    response = client.get("/api/signals/ticker/MSFT/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "MSFT"
    assert payload["signal"] in {"BUY", "HOLD", "SELL"}
