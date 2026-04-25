import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal

import yaml
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.market import MarketData
from app.schemas.market import (
    FreshnessInfo,
    FreshnessReport,
    IngestResponse,
    OHLCVRow,
    TickerInfo,
    TickerStats,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

_WATCHLIST_CACHE: list[dict] | None = None


def _load_watchlist() -> list[dict]:
    global _WATCHLIST_CACHE

    try:
        from ml.data_pipeline.watchlist import load_watchlist

        _WATCHLIST_CACHE = [
            {
                "ticker": item["ticker"],
                "name": item.get("name") or item["ticker"],
                "sector": item.get("sector") or "Unknown",
            }
            for item in load_watchlist()
        ]
        if _WATCHLIST_CACHE:
            return _WATCHLIST_CACHE
    except Exception:
        pass

    candidates = [
        Path(__file__).parents[4] / "config" / "watchlist.yaml",
        Path(__file__).parents[3] / "config" / "watchlist.yaml",
    ]
    for p in candidates:
        if p.exists():
            with open(p) as f:
                _WATCHLIST_CACHE = yaml.safe_load(f)["tickers"]
                return _WATCHLIST_CACHE

    # Fallback hardcoded list
    _WATCHLIST_CACHE = [
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
        {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology"},
        {"ticker": "META", "name": "Meta Platforms Inc.", "sector": "Communication"},
        {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "sector": "ETF"},
        {"ticker": "QQQ", "name": "Invesco QQQ Trust", "sector": "ETF"},
        {"ticker": "GLD", "name": "SPDR Gold Shares", "sector": "Commodity ETF"},
    ]
    return _WATCHLIST_CACHE


def get_watchlist_tickers() -> list[str]:
    return [item["ticker"] for item in _load_watchlist()]


# ---------------------------------------------------------------------------
# Freshness helpers
# ---------------------------------------------------------------------------


def _freshness_status(last_date: date | None) -> Literal["fresh", "stale", "missing"]:
    if last_date is None:
        return "missing"
    days_ago = (date.today() - last_date).days
    return "fresh" if days_ago <= 4 else "stale"  # 4 days covers weekends + holidays


# ---------------------------------------------------------------------------
# Market Service
# ---------------------------------------------------------------------------


class MarketService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Tickers
    # ------------------------------------------------------------------

    def get_tickers(self) -> list[TickerInfo]:
        watchlist = _load_watchlist()
        tickers = [w["ticker"] for w in watchlist]

        # Latest row per ticker (single query)
        subq = (
            self.db.query(
                MarketData.ticker, func.max(MarketData.date).label("max_date")
            )
            .filter(MarketData.ticker.in_(tickers))
            .group_by(MarketData.ticker)
            .subquery()
        )
        latest_rows = (
            self.db.query(MarketData)
            .join(
                subq,
                (MarketData.ticker == subq.c.ticker)
                & (MarketData.date == subq.c.max_date),
            )
            .all()
        )
        latest_map = {r.ticker: r for r in latest_rows}

        # Previous close for % change
        prev_subq = (
            self.db.query(
                MarketData.ticker, func.max(MarketData.date).label("prev_date")
            )
            .filter(
                MarketData.ticker.in_(tickers),
                ~(
                    MarketData.date.in_(
                        [r.date for r in latest_rows] if latest_rows else [date.today()]
                    )
                ),
            )
            .group_by(MarketData.ticker)
            .subquery()
        )
        prev_rows = (
            self.db.query(MarketData)
            .join(
                prev_subq,
                (MarketData.ticker == prev_subq.c.ticker)
                & (MarketData.date == prev_subq.c.prev_date),
            )
            .all()
        )
        prev_map = {r.ticker: r for r in prev_rows}

        result = []
        for w in watchlist:
            t = w["ticker"]
            latest = latest_map.get(t)
            prev = prev_map.get(t)

            change_pct: float | None = None
            if latest and prev and prev.close and float(prev.close) != 0:
                change_pct = (float(latest.close) - float(prev.close)) / float(prev.close) * 100

            result.append(
                TickerInfo(
                    ticker=t,
                    name=w.get("name", t),
                    sector=w.get("sector", ""),
                    last_date=latest.date if latest else None,
                    last_close=float(latest.close) if latest else None,
                    volume=latest.volume if latest else None,
                    freshness=_freshness_status(latest.date if latest else None),
                    change_pct=round(change_pct, 2) if change_pct is not None else None,
                )
            )
        return result

    # ------------------------------------------------------------------
    # OHLCV
    # ------------------------------------------------------------------

    def get_ohlcv(
        self,
        ticker: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> list[OHLCVRow]:
        q = (
            self.db.query(MarketData)
            .filter(MarketData.ticker == ticker.upper())
            .order_by(MarketData.date.asc())
        )
        if start_date:
            q = q.filter(MarketData.date >= start_date)
        if end_date:
            q = q.filter(MarketData.date <= end_date)
        if limit:
            # Apply limit from the end (most recent N rows)
            total = q.count()
            if total > limit:
                q = q.offset(total - limit)
        rows = q.all()
        return [
            OHLCVRow(
                date=r.date,
                open=float(r.open) if r.open is not None else None,
                high=float(r.high) if r.high is not None else None,
                low=float(r.low) if r.low is not None else None,
                close=float(r.close) if r.close is not None else None,
                adj_close=float(r.adj_close) if r.adj_close is not None else None,
                volume=r.volume,
            )
            for r in rows
        ]

    def get_latest(self, ticker: str) -> OHLCVRow | None:
        row = (
            self.db.query(MarketData)
            .filter(MarketData.ticker == ticker.upper())
            .order_by(MarketData.date.desc())
            .first()
        )
        if not row:
            return None
        return OHLCVRow(
            date=row.date,
            open=float(row.open) if row.open is not None else None,
            high=float(row.high) if row.high is not None else None,
            low=float(row.low) if row.low is not None else None,
            close=float(row.close) if row.close is not None else None,
            adj_close=float(row.adj_close) if row.adj_close is not None else None,
            volume=row.volume,
        )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, ticker: str) -> TickerStats:
        t = ticker.upper()
        today = date.today()
        year_ago = today - timedelta(days=365)
        jan1 = date(today.year, 1, 1)

        rows_52w = (
            self.db.query(MarketData)
            .filter(MarketData.ticker == t, MarketData.date >= year_ago)
            .all()
        )
        if not rows_52w:
            return TickerStats(ticker=t)

        closes = [float(r.close) for r in rows_52w if r.close is not None]
        volumes = [r.volume for r in rows_52w if r.volume is not None]

        latest = max(rows_52w, key=lambda r: r.date)
        current_price = float(latest.close) if latest.close else None

        # YTD return
        ytd_row = (
            self.db.query(MarketData)
            .filter(MarketData.ticker == t, MarketData.date >= jan1)
            .order_by(MarketData.date.asc())
            .first()
        )
        ytd_return: float | None = None
        if ytd_row and ytd_row.close and current_price:
            first_close = float(ytd_row.close)
            if first_close != 0:
                ytd_return = round((current_price - first_close) / first_close * 100, 2)

        all_dates = [r.date for r in rows_52w]
        return TickerStats(
            ticker=t,
            current_price=current_price,
            week52_high=round(max(closes), 4) if closes else None,
            week52_low=round(min(closes), 4) if closes else None,
            avg_volume=round(sum(volumes) / len(volumes)) if volumes else None,
            ytd_return=ytd_return,
            data_from=min(all_dates),
            data_to=max(all_dates),
        )

    # ------------------------------------------------------------------
    # Freshness
    # ------------------------------------------------------------------

    def get_freshness(self) -> FreshnessReport:
        tickers = get_watchlist_tickers()
        latest_rows = (
            self.db.query(MarketData.ticker, func.max(MarketData.date).label("max_date"))
            .filter(MarketData.ticker.in_(tickers))
            .group_by(MarketData.ticker)
            .all()
        )
        latest_map = {r.ticker: r.max_date for r in latest_rows}
        today = date.today()

        info: dict[str, FreshnessInfo] = {}
        for t in tickers:
            last = latest_map.get(t)
            days = (today - last).days if last else None
            info[t] = FreshnessInfo(
                ticker=t,
                status=_freshness_status(last),
                last_date=last,
                days_stale=days,
            )
        return FreshnessReport(tickers=info, checked_at=datetime.utcnow())

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, tickers: list[str] | None = None) -> IngestResponse:
        try:
            import pandas as pd
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError("yfinance/pandas not installed. Run: pip install yfinance pandas") from exc

        if tickers is None:
            tickers = get_watchlist_tickers()

        ingested: list[str] = []
        failed: list[str] = []
        total_new = 0

        for ticker in tickers:
            try:
                logger.info("Downloading %s …", ticker)
                df = yf.download(
                    ticker,
                    period="5y",
                    auto_adjust=False,
                    progress=False,
                    actions=False,
                )

                if df.empty:
                    logger.warning("%s: empty dataframe", ticker)
                    failed.append(ticker)
                    continue

                # Flatten MultiIndex columns (yfinance >=0.2.x)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)

                df = df.rename(
                    columns={
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Adj Close": "adj_close",
                        "Volume": "volume",
                    }
                )

                # Existing dates for this ticker
                existing = {
                    r[0]
                    for r in self.db.query(MarketData.date)
                    .filter(MarketData.ticker == ticker)
                    .all()
                }

                new_count = 0
                for ts, row in df.iterrows():
                    row_date = ts.date() if hasattr(ts, "date") else ts
                    if row_date in existing:
                        continue
                    md = MarketData(
                        ticker=ticker,
                        date=row_date,
                        open=_safe_float(row.get("open")),
                        high=_safe_float(row.get("high")),
                        low=_safe_float(row.get("low")),
                        close=_safe_float(row.get("close")),
                        adj_close=_safe_float(row.get("adj_close")),
                        volume=_safe_int(row.get("volume")),
                    )
                    self.db.add(md)
                    new_count += 1

                self.db.commit()
                total_new += new_count
                ingested.append(ticker)
                logger.info("%s: +%d rows", ticker, new_count)
                time.sleep(0.3)  # polite rate limit

            except Exception as exc:
                logger.error("%s: ingestion failed — %s", ticker, exc)
                self.db.rollback()
                failed.append(ticker)

        return IngestResponse(
            message=f"Ingested {len(ingested)}/{len(tickers)} tickers, {total_new} new rows",
            tickers_ingested=ingested,
            tickers_failed=failed,
            rows_added=total_new,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(val) -> float | None:
    try:
        v = float(val)
        return None if (v != v) else v  # NaN check
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    try:
        v = int(val)
        return None if v == 0 else v
    except (TypeError, ValueError):
        return None
