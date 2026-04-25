from __future__ import annotations


def test_market_tickers_returns_seeded_watchlist(client) -> None:
    response = client.get("/api/market/tickers")
    assert response.status_code == 200
    payload = response.json()
    assert [item["ticker"] for item in payload[:2]] == ["AAPL", "MSFT"]


def test_market_ohlcv_returns_rows_for_ticker(client) -> None:
    response = client.get("/api/market/ohlcv/AAPL?limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 5
    assert payload[-1]["close"] is not None


def test_market_latest_returns_latest_bar(client) -> None:
    response = client.get("/api/market/latest/MSFT")
    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] is not None
    assert payload["close"] > 0


def test_market_stats_returns_price_summary(client) -> None:
    response = client.get("/api/market/stats/AAPL")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["current_price"] > 0


def test_market_freshness_returns_report(client) -> None:
    response = client.get("/api/market/freshness")
    assert response.status_code == 200
    payload = response.json()
    assert "AAPL" in payload["tickers"]
    assert payload["tickers"]["MSFT"]["status"] in {"fresh", "stale", "missing"}
