# AlgoTrade Sentinel

**An end-to-end AI-powered trading research and MLOps platform.**

AlgoTrade Sentinel is a production-grade system that automates the entire quantitative trading research lifecycle — from raw market data ingestion through feature engineering, multi-model machine learning, backtesting, live signal generation, model monitoring, and paper portfolio simulation — all accessible through a modern React dashboard.

---
<img width="1919" height="946" alt="Screenshot 2026-04-26 193923" src="https://github.com/user-attachments/assets/fa9720a1-6419-4ac9-9f89-8e2528e63c21" />
<img width="1919" height="937" alt="Screenshot 2026-04-26 193954" src="https://github.com/user-attachments/assets/7a607ef8-7a08-49df-8a47-1e25cc0497ae" />
<img width="1912" height="945" alt="Screenshot 2026-04-26 194003" src="https://github.com/user-attachments/assets/19d9f9ce-135b-4780-bded-646781979201" />
<img width="1919" height="941" alt="Screenshot 2026-04-26 194850" src="https://github.com/user-attachments/assets/294fba6e-6b9d-46cf-b3cd-306f5d7f7cef" />
<img width="1883" height="889" alt="Screenshot 2026-04-26 194840" src="https://github.com/user-attachments/assets/41a750bc-d7f5-434d-89c8-eb7ea71837be" />
<img width="1918" height="955" alt="Screenshot 2026-04-26 194821" src="https://github.com/user-attachments/assets/d0c42e51-65e3-433e-b464-2a104d5b32fd" />
<img width="1916" height="888" alt="Screenshot 2026-04-26 194811" src="https://github.com/user-attachments/assets/aa7246a0-dad6-4149-9161-156a298454f7" />
<img width="1916" height="939" alt="Screenshot 2026-04-26 194759" src="https://github.com/user-attachments/assets/94a23af6-7865-4575-8250-909a6b987c4b" />
<img width="1908" height="934" alt="Screenshot 2026-04-26 194745" src="https://github.com/user-attachments/assets/78ac5fb0-c643-4045-a117-c68b257b9ddd" />
<img width="1899" height="910" alt="Screenshot 2026-04-26 194700" src="https://github.com/user-attachments/assets/a6267d64-7253-4eb7-9dbf-c37379a2b4b3" />
<img width="1918" height="868" alt="Screenshot 2026-04-26 194643" src="https://github.com/user-attachments/assets/4ca70809-dafb-4740-a10a-8f7c3bba4a51" />
<img width="1916" height="894" alt="Screenshot 2026-04-26 194633" src="https://github.com/user-attachments/assets/1fd7e70c-9953-484f-83ee-44b2a6164f8a" />
<img width="1919" height="763" alt="Screenshot 2026-04-26 194622" src="https://github.com/user-attachments/assets/a0bfd008-fb53-4bdd-8156-3ec80691e1cd" />
<img width="1919" height="853" alt="Screenshot 2026-04-26 194557" src="https://github.com/user-attachments/assets/f8d7c92e-5c58-4fa6-912d-bf39e959049f" />
<img width="1789" height="936" alt="Screenshot 2026-04-26 194538" src="https://github.com/user-attachments/assets/7ce2df59-aafa-4343-9518-fb378f13438c" />
<img width="1839" height="788" alt="Screenshot 2026-04-26 194450" src="https://github.com/user-attachments/assets/5b733dc0-69f0-4f1c-9c0d-259424dac151" />
<img width="1919" height="937" alt="Screenshot 2026-04-26 194243" src="https://github.com/user-attachments/assets/db8913d4-deea-4643-9840-3544bcaa037f" />
<img width="1917" height="966" alt="Screenshot 2026-04-26 194219" src="https://github.com/user-attachments/assets/1d587499-8a36-44c4-8908-24651a3dfc9e" />
<img width="1919" height="934" alt="Screenshot 2026-04-26 194204" src="https://github.com/user-attachments/assets/dc7468c5-1d0d-4086-99b9-d5e324c8a8c7" />
<img width="1919" height="965" alt="Screenshot 2026-04-26 194140" src="https://github.com/user-attachments/assets/5683ffe4-e497-4c0b-8837-76cac26d195d" />
<img width="1919" height="943" alt="Screenshot 2026-04-26 194128" src="https://github.com/user-attachments/assets/c5dab503-1419-4217-bbf4-a75ab8c51734" />
<img width="1919" height="945" alt="Screenshot 2026-04-26 194040" src="https://github.com/user-attachments/assets/b3191a0d-965c-497c-be37-11efec954a8d" />
<img width="1916" height="872" alt="Screenshot 2026-04-26 194023" src="https://github.com/user-attachments/assets/f5706407-f84a-4993-9c7b-94448040eafa" />
<img width="1912" height="945" alt="Screenshot 2026-04-26 194003" src="https://github.com/user-attachments/assets/19d9f9ce-135b-4780-bded-646781979201" />



## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [ML Pipeline](#ml-pipeline)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Production Deployment](#production-deployment)
- [Services & Ports](#services--ports)
- [Key Design Decisions](#key-design-decisions)

---

## Overview

AlgoTrade Sentinel implements a complete 10-phase ML trading pipeline:

| Phase | Component | Description |
|-------|-----------|-------------|
| 1 | Infrastructure | FastAPI + Next.js + PostgreSQL + Docker stack |
| 2 | Market Data | yfinance ingestion → OHLCV in PostgreSQL |
| 3 | Feature Engineering | 35 technical indicators (trend, momentum, volatility, volume, price action) |
| 4 | Model Training | 6+ classifiers with Optuna HPO, MLflow tracking |
| 5 | Backtesting | Event-driven backtest engine with 15 financial metrics |
| 6 | Signals & Registry | Batch inference, champion/challenger model lifecycle |
| 7 | Monitoring | Evidently drift detection, performance tracking, auto-retraining |
| 8 | Portfolio | Paper trading with signal-based order execution |
| 9 | Alerts | Rule-based alert engine with severity levels |
| 10 | Convention | Standardised API envelope, TimestampMixin, ORM-only queries |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser / Client                         │
│              Next.js 14  ·  TypeScript  ·  Tailwind             │
│         React Query  ·  Recharts  ·  Lightweight Charts         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP (REST)
┌───────────────────────────▼─────────────────────────────────────┐
│                      FastAPI Backend                            │
│   14 routers · Pydantic v2 · SQLAlchemy 2 · Alembic · ORM-only │
│       APScheduler (cron jobs) · SlowAPI (rate limiting)         │
└───┬───────────────┬───────────────┬─────────────────────────────┘
    │               │               │
    ▼               ▼               ▼
┌───────┐     ┌──────────┐   ┌──────────────────────────────────┐
│  DB   │     │  MLflow  │   │         ML Layer                  │
│Postgre│     │  :5000   │   │  trainer · inference · backtest   │
│ :5432 │     │ Tracking │   │  monitor · portfolio · registry   │
└───────┘     │ Registry │   └──────────────────────────────────┘
              │Artifacts │
              └──────────┘
                    │
              ┌──────────┐
              │ Prefect  │
              │  :4200   │
              │Workflow  │
              │Orchestrat│
              └──────────┘
```

### Startup Order

```
db (postgres) ──healthy──► mlflow  ──healthy──►
                  └───────► prefect ──healthy──► backend ──started──► frontend
```

---

## Features

### Machine Learning
- **6+ Classifiers** — LogisticRegression, DecisionTree, RandomForest, GradientBoosting, XGBoost, LightGBM, CatBoost
- **Optuna HPO** — 20 Bayesian trials per model, TPE sampler, fully seed-reproducible (seed=42)
- **Time-Series Cross Validation** — 5-fold to prevent look-ahead bias
- **3-Class Signal Labels** — BUY / HOLD / SELL (based on 5-day forward returns)
- **35 Technical Indicators** — Across trend, momentum, volatility, volume, and price-action groups
- **Feature Importance** — Permutation-based importance logged as MLflow metrics

### MLOps
- **Experiment Tracking** — Every run logged to MLflow with params, metrics, confusion matrix, artifacts, and sklearn model
- **Model Registry** — Champion/challenger lifecycle with automated F1-delta promotion (threshold: 1%)
- **Drift Detection** — Daily Evidently reports covering feature drift and prediction distribution drift
- **Auto-Retraining** — Triggered when drift exceeds 15% or F1 degrades >10%, with 7-day cooldown

### Trading
- **Backtesting Engine** — Event-driven simulation with $100k capital, 0.1% transaction cost, 0.05% slippage
- **15 Financial Metrics** — Sharpe, Sortino, Calmar, max drawdown, win rate, profit factor, alpha, and more
- **Paper Portfolio** — Signal-based order execution with position tracking and daily snapshots
- **Alert Engine** — Rule-based alerts with INFO / WARNING / CRITICAL severity levels

### Infrastructure
- **Standard API Envelope** — `{ "data": ..., "meta": { "timestamp", "version" } }` on every response
- **Consistent Errors** — `{ "error": { "code", "message", "details" } }` on every failure
- **ORM-Only Queries** — No raw SQL in services — all database access through SQLAlchemy ORM
- **TimestampMixin** — `created_at` and `updated_at` auto-managed by PostgreSQL on all 14 tables
- **Rate Limiting** — SlowAPI middleware (120 req/min default)

---

## Tech Stack

### Backend

| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.5 | REST API framework |
| Uvicorn | 0.32.1+ | ASGI server |
| SQLAlchemy | 2.0.36 | ORM |
| Alembic | 1.14.0 | Database migrations |
| Pydantic | 2.10.3+ | Request / response validation |
| psycopg2-binary | 2.9.10 | PostgreSQL driver |
| APScheduler | 3.10.4+ | Cron job scheduler |
| slowapi | 0.1.9+ | Rate limiting |

### Frontend

| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.2.15 | React framework (App Router) |
| React | 18 | UI library |
| TypeScript | 5 | Type safety |
| Tailwind CSS | 3.4.14 | Utility-first styling |
| TanStack React Query | 5.59.0 | Server state management |
| TanStack React Table | 8.20.5 | Data grid |
| Zustand | 5.0.0 | Global state |
| Recharts | 2.13.3 | Chart library |
| Lightweight Charts | 4.2.0 | Financial candlestick charts |
| React Hook Form | 7.53.0 | Form management |
| Zod | 3.23.8 | Schema validation |

### ML / MLOps

| Package | Version | Purpose |
|---------|---------|---------|
| scikit-learn | 1.4.0+ | Core ML models |
| XGBoost | 2.0.0+ | Gradient boosting |
| LightGBM | 4.3.0+ | Gradient boosting |
| CatBoost | latest | Gradient boosting |
| Optuna | 3.6.0 | Hyperparameter optimisation |
| MLflow | 2.13.0+ | Experiment tracking & model registry |
| Evidently | 0.4.0+ | Data / model drift detection |
| yfinance | 0.2.40+ | Market data ingestion |
| pandas | 2.0.0+ | Data manipulation |
| numpy | 1.24.0+ | Numerical operations |

### Infrastructure

| Service | Image | Purpose |
|---------|-------|---------|
| PostgreSQL | postgres:15-alpine | Primary database (app + Prefect) |
| MLflow | ghcr.io/mlflow/mlflow:v2.19.0 | Experiment tracking + artifact proxy |
| Prefect | prefecthq/prefect:2.19.9-python3.11 | Workflow orchestration |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) v4.0+
- [Docker Compose](https://docs.docker.com/compose/) v2.0+ (included with Docker Desktop)
- Git

> No local Python or Node.js installation required — everything runs inside containers.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/MohdAnasAnsari/AlgoTrade-Sentinel.git
cd AlgoTrade-Sentinel
```

### 2. Configure environment

```bash
cp .env.example .env
# Defaults work for local development — no changes needed to get started
```

### 3. Start the full stack

```bash
docker compose -f docker-compose.dev.yml up --build
```

> First run pulls ~2 GB of images and builds containers. Subsequent starts are fast.

Wait until all services are healthy. You will see:

```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | ✓ Ready in X.Xs
```

### 4. Access the services

| Service | URL |
|---------|-----|
| **Frontend Dashboard** | http://localhost:3000 |
| **Swagger API Docs** | http://localhost:8000/docs |
| **ReDoc API Reference** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |
| **MLflow UI** | http://localhost:5000 |
| **Prefect UI** | http://localhost:4200 |

### 5. Run the full ML pipeline

Open a shell in the backend container and run the bootstrap script:

```bash
docker compose -f docker-compose.dev.yml exec backend bash /app/scripts/demo_setup.sh
```

This runs all pipeline stages in sequence:
1. Market data ingest (10 tickers, 2 years of daily OHLCV from Yahoo Finance)
2. Feature engineering (35 technical indicators)
3. Label creation (BUY/HOLD/SELL via 5-day forward returns)
4. Dataset build (versioned parquet export)
5. Model training (all classifiers + Optuna HPO, logged to MLflow)
6. Backtest run
7. Signal generation

### 6. Trigger individual stages via API

```bash
# Ingest market data
curl -X POST http://localhost:8000/api/market/ingest

# Run feature engineering
curl -X POST http://localhost:8000/api/features/run

# Start model training (returns job_id immediately — training runs in background)
curl -X POST http://localhost:8000/api/training/run \
  -H "Content-Type: application/json" \
  -d '{"dataset_version": 1, "run_name": "my_run", "n_optuna_trials": 20}'

# Poll training status
curl http://localhost:8000/api/training/status/<job_id>

# Run batch inference (generate signals)
curl -X POST http://localhost:8000/api/signals/run

# Run backtest
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"initial_capital": 100000}'
```

---

## Project Structure

```
AlgoTrade-Sentinel/
│
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app entry point, error handlers
│   │   ├── config.py                   # Pydantic Settings (env var parsing)
│   │   ├── database.py                 # SQLAlchemy engine + session factory
│   │   ├── middleware.py               # CORS, security headers, request logging
│   │   ├── scheduler.py                # APScheduler cron job definitions
│   │   ├── core/
│   │   │   └── response.py             # ok() helper — StandardResponse envelope
│   │   ├── models/
│   │   │   ├── __init__.py             # Base + TimestampMixin
│   │   │   ├── market.py               # MarketData
│   │   │   ├── features.py             # FeaturesData, LabelsData, DatasetVersion
│   │   │   ├── backtest.py             # BacktestResult
│   │   │   ├── signals.py              # Signal, ModelRegistryLog
│   │   │   ├── monitoring.py           # MonitoringReport, RetrainLog
│   │   │   ├── portfolio.py            # Position, Order, PortfolioSnapshot, Alert, Watchlist
│   │   │   └── settings.py             # AppSettings
│   │   ├── routers/                    # 14 FastAPI routers (one per domain)
│   │   │   ├── health.py  system.py  market.py  features.py
│   │   │   ├── dashboard.py  training.py  backtest.py  signals.py
│   │   │   ├── registry.py  monitoring.py  portfolio.py
│   │   │   ├── alerts.py  watchlist.py  settings.py
│   │   └── services/                   # Business logic (one file per domain)
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                   # 9 sequential migration files
│   ├── tests/                          # pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                  # Root layout with QueryProvider
│   │   ├── page.tsx                    # Home (redirects to /dashboard)
│   │   ├── (main)/                     # Route group with sidebar navigation
│   │   │   ├── dashboard/
│   │   │   ├── market-explorer/
│   │   │   ├── signal-center/
│   │   │   ├── training-lab/
│   │   │   ├── model-registry/
│   │   │   ├── backtesting-center/
│   │   │   ├── monitoring-center/
│   │   │   ├── paper-portfolio/
│   │   │   ├── strategy-lab/
│   │   │   ├── settings/
│   │   │   └── help-docs/
│   │   └── api/                        # Next.js server-side API routes
│   ├── components/                     # Shared React components
│   ├── hooks/                          # Custom React hooks
│   ├── lib/
│   │   ├── api.ts                      # Fetch wrapper with envelope unwrapping
│   │   └── store.ts                    # Zustand global store
│   ├── providers/
│   │   └── query-provider.tsx          # React Query + DevTools
│   ├── package.json
│   └── Dockerfile
│
├── ml/
│   ├── data_pipeline/
│   │   ├── ingest.py                   # yfinance → market_data table
│   │   ├── freshness.py                # Data freshness checker
│   │   └── watchlist.py                # DB/YAML watchlist loader
│   ├── features/
│   │   ├── feature_engineer.py         # 35 technical indicators
│   │   ├── label_builder.py            # BUY/HOLD/SELL label creation
│   │   └── dataset_builder.py          # Parquet dataset builder
│   ├── training/
│   │   ├── trainer.py                  # Multi-model training + Optuna HPO
│   │   ├── mlflow_logger.py            # MLflow experiment/artifact logging
│   │   └── explainability.py           # Permutation feature importance
│   ├── inference/
│   │   └── batch_predictor.py          # Batch signal prediction
│   ├── backtesting/
│   │   ├── backtest_engine.py          # Event-driven backtest engine
│   │   └── inference.py                # Historical inference helper
│   ├── monitoring/
│   │   ├── drift_detector.py           # Evidently drift detection
│   │   └── retrain_trigger.py          # Auto-retrain decision logic
│   ├── portfolio/
│   │   ├── paper_trader.py             # Paper trading execution
│   │   └── alerts_engine.py            # Alert rule evaluation
│   ├── registry/
│   │   └── registry_manager.py         # Champion/challenger promotion
│   ├── artifacts/
│   │   ├── datasets/                   # Versioned parquet datasets
│   │   ├── models/                     # Saved model pickle files per run
│   │   └── monitoring/                 # Evidently HTML drift reports
│   └── requirements.txt
│
├── config/
│   └── ml_config.yaml                  # ML thresholds, HPO search spaces, defaults
│
├── scripts/
│   ├── init_db.sh                      # DB init script (runs at container startup)
│   ├── demo_setup.sh                   # Full pipeline demo bootstrap
│   ├── seed_data.sh                    # Test data seeder
│   ├── start_flows.sh                  # Prefect flow registration
│   └── restore_mlflow_registry.py      # MLflow registry restore utility
│
├── docker-compose.yml                  # Production stack
├── docker-compose.dev.yml              # Development stack (hot-reload, bind mounts)
├── .env.example                        # Environment variable template
├── .gitignore
├── Makefile
└── README.md
```

---

## ML Pipeline

### Stage 1 — Market Data Ingestion

- **Source**: Yahoo Finance (`yfinance`)
- **Stores**: daily OHLCV in `market_data` table — ticker, date, open, high, low, close, adj_close, volume
- **Incremental**: only fetches dates after the last stored row per ticker
- **Alert**: data freshness check raises WARNING if any ticker is >3 days stale

### Stage 2 — Feature Engineering

35 technical indicators stored in `features_data`:

| Group | Count | Features |
|-------|-------|---------|
| **Trend** | 13 | sma_10/20/50/200, ema_10/20/50, macd_line/signal/hist, adx_14, price_vs_sma20_pct, price_vs_sma50_pct |
| **Momentum** | 5 | rsi_14, stoch_k, stoch_d, roc_10, williams_r |
| **Volatility** | 6 | bb_upper, bb_lower, bb_width, bb_pct_b, atr_14, hist_vol_20 |
| **Volume** | 4 | obv, vol_sma_20, vol_ratio, cmf_20 |
| **Price Action** | 7 | daily_return, return_3d/5d/10d, gap_pct, hl_range_pct, candle_body_pct |

### Stage 3 — Label Creation

5-day forward-looking return labelling (stored in `labels_data`):

| Label | Condition |
|-------|-----------|
| **BUY** | 5-day return > +2% |
| **SELL** | 5-day return < −2% |
| **HOLD** | 5-day return in [−2%, +2%] |

Datasets are also exported as versioned parquet files to `ml/artifacts/datasets/`.

### Stage 4 — Model Training

```
dataset_v{N}.parquet
    → StandardScaler (fit on train only, transform both splits)
    → Time-series split by date (rows before split_date = train, after = test)
    ↓
For each classifier (up to 7):
    ├── [Optional] Optuna HPO
    │       20 trials · TPE sampler (seed=42) · 5-fold TimeSeriesSplit · F1-macro objective
    ├── model.fit(X_train, y_train)
    ├── Evaluate: accuracy, precision, recall, F1-macro, ROC-AUC (macro OvR)
    ├── Compute permutation feature importances
    └── Log to MLflow:
            params · metrics · confusion matrix · classification report
            feature importances · model.pkl · scaler.pkl · features.json
    ↓
Best model (highest F1-macro) → register to MLflow Model Registry (Staging stage)
```

**Reproducibility**: `random.seed(42)`, `np.random.seed(42)`, `TPESampler(seed=42)` on all Optuna studies.

### Stage 5 — Backtesting

Event-driven portfolio simulation:

| Parameter | Default |
|-----------|---------|
| Initial capital | $100,000 |
| Transaction cost | 0.1% per trade |
| Slippage | 0.05% |
| Position sizing | 10% of portfolio per signal |

**Output metrics**: total return, annualised return, benchmark return, alpha, Sharpe ratio, Sortino ratio, Calmar ratio, max drawdown, daily volatility, win rate, profit factor, avg win/loss, total trades, avg holding days. Equity curve, drawdown curve, and full trade log stored as JSON blobs.

### Stage 6 — Batch Inference & Signal Generation

1. Loads Production champion model from MLflow registry
2. Runs predictions on latest feature rows for each watchlist ticker
3. Emits signal only when `max(class_probabilities) >= 0.55`
4. Stores in `signals` table: ticker, signal_date, signal_type (BUY/HOLD/SELL), confidence, model_version

### Stage 7 — Model Monitoring

Daily Evidently reports stored in `monitoring_reports`:

| Check | Threshold | Action |
|-------|-----------|--------|
| Feature drift (JS divergence) | >15% of features | Alert WARNING |
| Prediction distribution drift | >15% ratio change | Alert WARNING |
| F1 performance degradation | >10% drop from baseline | Trigger retrain |
| Data freshness | >3 days stale | Alert WARNING |

Auto-retrain cooldown: 7 days (prevents cascading retrains). All retrain events logged to `retrain_logs`.

### Stage 8 — Paper Portfolio

- Executes buy/sell orders based on signals
- Tracks open positions with entry price, current price, unrealised P&L
- Creates daily `portfolio_snapshots` (total value, cash balance, invested, realised/unrealised P&L)
- Generates `alerts` for large drawdowns, missed signals, data staleness

---

## API Reference

All successful responses use the standard envelope:
```json
{
  "data": { "...": "..." },
  "meta": {
    "timestamp": "2026-04-26T10:00:00+00:00",
    "version": "0.1.0"
  }
}
```

All errors:
```json
{
  "error": {
    "code": 422,
    "message": "Validation error",
    "details": {}
  }
}
```

### Health & System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Backend health — status, version, environment, scheduler state |
| GET | `/api/system/status` | Full system check including DB connectivity |

### Market Data — `/api/market`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/market/tickers` | All tickers stored in the database |
| GET | `/api/market/ohlcv/{ticker}` | OHLCV candles (params: start_date, end_date, limit) |
| GET | `/api/market/latest/{ticker}` | Most recent OHLCV row |
| GET | `/api/market/stats/{ticker}` | Aggregated stats (52w high/low, avg volume) |
| GET | `/api/market/freshness` | Data freshness per ticker |
| POST | `/api/market/ingest` | Trigger yfinance ingestion job |

### Features & Datasets — `/api/features`, `/api/labels`, `/api/dataset`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/features/list/{ticker}` | Latest N rows of computed features |
| GET | `/api/features/stats/{ticker}` | Per-column statistics |
| POST | `/api/features/run` | Run full feature engineering pipeline |
| GET | `/api/labels/distribution` | Label class counts across all tickers |
| GET | `/api/labels/distribution/{ticker}` | Label distribution for one ticker |
| GET | `/api/dataset/versions` | All versioned datasets |
| GET | `/api/dataset/{version}/summary` | Dataset metadata (rows, split date, features list) |

### Model Training — `/api/training`, `/api/experiments`, `/api/models`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/training/run` | Start background training job (returns job_id immediately) |
| GET | `/api/training/status/{job_id}` | Poll status — running / complete / failed |
| GET | `/api/experiments/list` | All MLflow runs (newest first, with key metrics) |
| GET | `/api/experiments/best` | Best run by F1 macro |
| GET | `/api/experiments/{run_id}` | Full run detail — metrics, confusion matrix, classification report |
| GET | `/api/models/registry` | All registered MLflow models |
| GET | `/api/models/{model_name}/versions` | All versions of a registered model |
| GET | `/api/models/{run_id}/importance` | Top-20 feature importances for a run |

**Training request body:**
```json
{
  "dataset_version": 1,
  "model_list": null,
  "run_name": "production_run_v1",
  "n_optuna_trials": 20
}
```

### Signals & Inference — `/api/signals`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/signals/run` | Trigger batch inference on all watchlist tickers |
| GET | `/api/signals/status/{job_id}` | Poll inference job status |
| GET | `/api/signals/latest` | Latest signal per ticker (optional: filter by type) |
| GET | `/api/signals/history/{ticker}` | Signal history for one ticker (newest first) |
| GET | `/api/signals/ticker/{ticker}/latest` | Latest single signal for one ticker |
| GET | `/api/signals/{signal_id}` | Single signal by ID |

### Backtesting — `/api/backtest`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/backtest/run` | Start backtest job |
| GET | `/api/backtest/status/{job_id}` | Poll backtest status |
| GET | `/api/backtest/runs` | List all backtest run summaries |
| GET | `/api/backtest/compare` | Compare multiple runs (query param: run_ids) |
| GET | `/api/backtest/{run_id}` | Full backtest detail |
| GET | `/api/backtest/{run_id}/metrics` | Financial metrics only |
| GET | `/api/backtest/{run_id}/equity` | Equity curve data points |
| GET | `/api/backtest/{run_id}/drawdown` | Drawdown curve data points |
| GET | `/api/backtest/{run_id}/trades` | Full trade log |

### Model Registry — `/api/registry`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/registry/models` | All registered models |
| GET | `/api/registry/models/{name}/champion` | Current Production model |
| GET | `/api/registry/models/{name}/challengers` | Staging challengers |
| GET | `/api/registry/models/{name}/versions` | All versions |
| GET | `/api/registry/models/{name}/compare` | Champion vs challengers side-by-side |
| POST | `/api/registry/models/{name}/promote` | Promote a version to Production |
| POST | `/api/registry/models/{name}/archive` | Archive a version |
| POST | `/api/registry/models/{name}/auto-promote` | Auto-promote if F1 delta ≥ 0.01 |
| GET | `/api/registry/log` | Promotion audit log |

### Monitoring — `/api/monitoring`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/monitoring/latest` | Latest monitoring summary |
| GET | `/api/monitoring/history` | Historical reports (query: days) |
| GET | `/api/monitoring/drift/data` | Feature drift summary |
| GET | `/api/monitoring/drift/features` | Per-feature drift scores |
| GET | `/api/monitoring/drift/predictions` | Prediction distribution drift |
| GET | `/api/monitoring/performance` | Model performance tracking over time |
| GET | `/api/monitoring/freshness` | Data freshness status |
| GET | `/api/monitoring/alerts` | Active monitoring alerts |
| POST | `/api/monitoring/retrain` | Manually trigger retraining |
| GET | `/api/monitoring/retrain/history` | Retrain event log |

### Portfolio — `/api/portfolio`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/portfolio/summary` | Overview — total value, cash, invested, P&L |
| GET | `/api/portfolio/positions` | All open positions |
| GET | `/api/portfolio/positions/{ticker}` | Position detail with order history |
| GET | `/api/portfolio/orders` | Order history (params: limit, offset, order_type, ticker) |
| GET | `/api/portfolio/history` | Portfolio value over time (param: days) |
| GET | `/api/portfolio/pnl` | P&L breakdown — realised vs unrealised |

### Alerts & Watchlist — `/api/alerts`, `/api/watchlist`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/alerts/` | List alerts (params: limit, offset, severity, unread_only) |
| GET | `/api/alerts/unread` | Unread alert count |
| POST | `/api/alerts/{alert_id}/read` | Mark single alert as read |
| POST | `/api/alerts/read-all` | Mark all alerts as read |
| GET | `/api/watchlist/` | List all watched tickers |
| POST | `/api/watchlist/add` | Add a ticker to the watchlist |
| DELETE | `/api/watchlist/{ticker}` | Remove a ticker from the watchlist |

### Dashboard & Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard/overview` | Aggregated dashboard metrics |
| GET | `/api/settings` | Application configuration |
| POST | `/api/settings` | Update application configuration |

---

## Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Redirect to `/dashboard` |
| `/dashboard` | Dashboard | Portfolio summary, signal counts, recent activity widgets |
| `/market-explorer` | Market Explorer | Candlestick chart with indicator overlay, OHLCV table, data freshness |
| `/signal-center` | Signal Center | Live BUY/HOLD/SELL signals with confidence scores and history |
| `/training-lab` | Training Lab | Launch training jobs, compare experiment runs, feature importance charts |
| `/model-registry` | Model Registry | Champion/challenger management, promote/archive model versions |
| `/backtesting-center` | Backtesting Center | Configure and run backtests, equity curve, drawdown chart, trade log |
| `/monitoring-center` | Monitoring Center | Feature drift, prediction drift, performance tracking, retrain log |
| `/paper-portfolio` | Paper Portfolio | Open positions, order history, portfolio value chart, P&L breakdown |
| `/strategy-lab` | Strategy Lab | Feature engineering explorer, label distribution, dataset builder |
| `/settings` | Settings | Application and scheduler configuration |
| `/help-docs` | Help & Docs | Usage guide and documentation |

---

## Database Schema

All 14 tables include `created_at` and `updated_at` (set by PostgreSQL `CURRENT_TIMESTAMP`, managed via `TimestampMixin`).

```
market_data          ticker, date, open, high, low, close, adj_close, volume
features_data        ticker, date, [35 indicator columns]
labels_data          ticker, date, forward_return_5d, signal_label
dataset_versions     version, name, description, split_date, row_count, feature_list

signals              ticker, signal_date, signal_type, confidence, probabilities, model_version
model_registry_logs  action, model_name, old_version, new_version, f1_before, f1_after

backtest_results     run_name, model_version, initial_capital, metrics_json,
                     equity_curve_json, drawdown_json, trades_json, monthly_returns_json

monitoring_reports   report_date, report_type, drift_share, drifted_features_json,
                     prediction_drift_detected, model_perf_f1, alert_level, evidently_report_html
retrain_logs         triggered_at, trigger_reason, old_model_version, new_model_version,
                     new_f1, promoted

positions            ticker, entry_date, entry_price, shares, current_price,
                     unrealized_pnl, unrealized_pnl_pct, status, company_name, sector
orders               ticker, order_date, order_type, price, shares, total_value,
                     transaction_cost, signal_id
portfolio_snapshots  snapshot_date, total_value, cash_balance, invested_value,
                     total_pnl, total_pnl_pct, realized_pnl, unrealized_pnl
alerts               alert_type, ticker, message, severity, is_read
watchlists           ticker, company_name, sector, is_active

app_settings         category, key, value_json
```

### Migration Chain (Alembic)

```
f4e3d2c1b0a9  create_market_data
    ↓
b2c3d4e5f6a7  create_features_labels
    ↓
c3d4e5f6a7b8  create_backtest_results
    ↓
d4e5f6a7b8c9  create_signals_registry
    ↓
e5f6a7b8c9d0  create_monitoring_tables
    ↓
f6a7b8c9d0e1  create_portfolio_tables
    ↓
a7b8c9d0e1f2  create_app_settings_table
    ↓
g7h8i9j0k1l2  finalize_conventions  (rename tables, add updated_at)
    ↓
h8i9j0k1l2m3  add_created_at_to_watchlists
```

---

## Environment Variables

Copy `.env.example` to `.env`. All defaults work for local development.

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AlgoTrade Sentinel` | Application display name |
| `APP_VERSION` | `0.1.0` | Semantic version string |
| `ENVIRONMENT` | `development` | Runtime mode (development / staging / production) |
| `DEBUG` | `false` | Enable debug logging |
| `DATABASE_URL` | `postgresql://algotrade:algotrade@db:5432/algotrade` | SQLAlchemy connection string |
| `SECRET_KEY` | `change-me-in-production` | Secret key — **change in production** |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend origin (used in CORS) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON array of allowed CORS origins |
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000` | MLflow server address |
| `PREFECT_API_URL` | `http://prefect:4200/api` | Prefect server API URL |
| `ENABLE_APSCHEDULER` | `false` | Enable APScheduler background cron jobs |
| `INGEST_CRON` | `15 22 * * 1-5` | Market data ingest schedule (4:15 PM UTC, weekdays) |
| `FEATURE_CRON` | `30 22 * * 1-5` | Feature engineering schedule |
| `INFERENCE_CRON` | `45 22 * * 1-5` | Batch inference schedule |
| `MONITORING_CRON` | `0 23 * * 1-5` | Monitoring report schedule |
| `RATE_LIMIT_DEFAULT` | `120/minute` | Default API rate limit |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `GIT_PYTHON_REFRESH` | `quiet` | Silence GitPython startup messages |
| `MPLCONFIGDIR` | `/tmp/matplotlib` | Matplotlib config cache directory |
| `PREFECT_HOME` | `/tmp/.prefect` | Prefect home directory |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL (browser-side) |
| `INTERNAL_API_URL` | `http://backend:8000` | Backend API URL (server-side SSR) |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `algotrade` | PostgreSQL database name |
| `POSTGRES_USER` | `algotrade` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `algotrade` | PostgreSQL password — **change in production** |

---

## Running Tests

```bash
# Run the full test suite inside the backend container
docker compose -f docker-compose.dev.yml exec backend pytest

# Verbose output
docker compose -f docker-compose.dev.yml exec backend pytest -v

# Specific file
docker compose -f docker-compose.dev.yml exec backend pytest backend/tests/test_health.py

# With coverage
docker compose -f docker-compose.dev.yml exec backend pytest --cov=app --cov-report=term-missing
```

---

## Production Deployment

### 1. Update `.env` for production

```bash
SECRET_KEY=<strong-random-secret>
ENVIRONMENT=production
DEBUG=false
POSTGRES_PASSWORD=<strong-password>
CORS_ORIGINS=["https://yourdomain.com"]
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
ENABLE_APSCHEDULER=true
```

### 2. Start the production stack

```bash
docker compose up --build -d
```

Production additions vs dev:
- `restart: unless-stopped` on all services
- Full healthchecks on all 5 services
- Backend waits for all services to be healthy before starting
- APScheduler enabled for automated nightly pipeline runs

### 3. Verify

```bash
docker compose ps                        # All containers should be healthy
curl http://localhost:8000/health        # Should return {"data":{"status":"healthy",...}}
```

---

## Services & Ports

| Service | Port | Health Check Endpoint | Notes |
|---------|------|-----------------------|-------|
| **Frontend** | 3000 | HTTP 200 on `/` | Next.js dev or production build |
| **Backend** | 8000 | `GET /health` | FastAPI + Uvicorn |
| **PostgreSQL** | 5432 | `pg_isready` | Stores app data + Prefect state |
| **MLflow** | 5000 | HTTP `< 500` on `/` | Tracking server + artifact proxy |
| **Prefect** | 4200 | `GET /api/health` | Workflow orchestration server |

---

## Key Design Decisions

**ORM-Only Database Access**
All queries go through SQLAlchemy ORM — no raw SQL strings anywhere in the service layer. This enforces type safety, prevents SQL injection, and makes intent explicit in code review.

**Standard Response Envelope**
Every API response is wrapped in `{ "data": ..., "meta": { "timestamp", "version" } }`. The frontend `unwrap<T>()` helper handles this transparently, so TypeScript types are clean at the call site.

**TimestampMixin**
All 14 tables inherit `TimestampMixin` which adds `created_at` and `updated_at` with `server_default=func.now()`. Timestamps are set by PostgreSQL — never by Python — ensuring consistency across bulk inserts and migrations.

**MLflow Proxy Artifacts**
MLflow is configured with `--serve-artifacts --artifacts-destination /mlflow/artifacts`. Artifact uploads are proxied through the HTTP server (URI scheme: `mlflow-artifacts://`). The backend container never writes directly to the MLflow volume, eliminating cross-container permission issues.

**Prefect on PostgreSQL**
Prefect is configured with `PREFECT_API_DATABASE_CONNECTION_URL` pointing to PostgreSQL. The default SQLite backend causes `database is locked` errors when Prefect's multiple async internal services (scheduler, telemetry, flow-run notifications, loop service) write concurrently. PostgreSQL handles concurrent writes correctly.

**Seed Reproducibility**
`random.seed(42)`, `np.random.seed(42)`, and `TPESampler(seed=42)` on every Optuna study. Given the same dataset version and split date, training results are fully reproducible.

**Background Training Jobs**
Training runs in a daemon thread with in-memory status tracking (job_id → status dict). The `/api/training/run` endpoint returns a `job_id` immediately and the client polls `/api/training/status/{job_id}`. This prevents HTTP timeouts on long training jobs (20+ Optuna trials × 6 models can take 5–30 minutes).

---

## Disclaimer

This project is for **educational and research purposes only**. Nothing in this repository constitutes financial advice. All trading signals, backtests, and portfolio simulations are for research only. Do not use with real capital without independent validation, regulatory compliance review, and appropriate risk management.

---

*Built with FastAPI · Next.js · PostgreSQL · MLflow · Prefect · scikit-learn · XGBoost · LightGBM · Evidently*
