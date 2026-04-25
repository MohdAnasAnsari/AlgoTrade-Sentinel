#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/backend:$ROOT_DIR:${PYTHONPATH:-}"

echo "[demo] initializing database tables"
python - <<'PY'
from app.database import init_database
init_database()
PY

echo "[demo] seeding watchlist"
python - <<'PY'
from app.database import SessionLocal
from app.models.portfolio import Watchlist

db = SessionLocal()
try:
    defaults = [
        ("AAPL", "Apple Inc.", "Technology"),
        ("MSFT", "Microsoft Corp.", "Technology"),
        ("TSLA", "Tesla Inc.", "Consumer Cyclical"),
        ("NVDA", "NVIDIA Corp.", "Technology"),
        ("SPY", "SPDR S&P 500 ETF", "ETF"),
    ]
    for ticker, name, sector in defaults:
        row = db.query(Watchlist).filter(Watchlist.ticker == ticker).first()
        if row is None:
            db.add(Watchlist(ticker=ticker, company_name=name, sector=sector, is_active=True))
        else:
            row.company_name = name
            row.sector = sector
            row.is_active = True
    db.commit()
finally:
    db.close()
PY

echo "[demo] ingesting market data"
python - <<'PY'
from app.database import SessionLocal
from app.services.market_service import MarketService

db = SessionLocal()
try:
    result = MarketService(db).ingest(["AAPL", "MSFT", "TSLA", "NVDA", "SPY"])
    print(result.message)
finally:
    db.close()
PY

echo "[demo] building features and labels"
python - <<'PY'
from app.database import SessionLocal
from app.services.feature_service import FeatureService

db = SessionLocal()
try:
    result = FeatureService(db).run_pipeline(
        tickers=["AAPL", "MSFT", "TSLA", "NVDA", "SPY"],
        build_ds=True,
    )
    print(result.message)
finally:
    db.close()
PY

echo "[demo] optional fast training run"
python - <<'PY'
from app.services.training_service import start_training_job, get_job_status
from app.database import SessionLocal
from app.models.features import DatasetVersion
import time

db = SessionLocal()
try:
    latest = db.query(DatasetVersion).order_by(DatasetVersion.version.desc()).first()
    if latest is None:
        print("No dataset version available; skipping training.")
    else:
        job_id = start_training_job(
            dataset_version=latest.version,
            model_list=None,
            run_name="demo-fast-run",
            n_optuna_trials=10,
        )
        for _ in range(180):
            status = get_job_status(job_id)
            if status and status["status"] in {"complete", "failed"}:
                print(status["message"])
                break
            time.sleep(5)
except Exception as exc:
    print(f"Training skipped: {exc}")
finally:
    db.close()
PY

echo "[demo] rebuilding paper portfolio"
python - <<'PY'
from app.database import SessionLocal
from app.services.portfolio_service import rebuild_portfolio_state

db = SessionLocal()
try:
    rebuild_portfolio_state(db)
    print("Paper portfolio rebuilt.")
finally:
    db.close()
PY

echo "[demo] complete"
