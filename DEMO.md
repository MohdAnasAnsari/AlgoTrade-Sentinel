# Demo Walkthrough

## Goal

Show AlgoTrade Sentinel as a polished end-to-end trading research and MLOps product in 10 to 15 minutes.

## Demo Setup

Run one of:

```bash
make seed
scripts/demo_setup.sh
```

## Recommended Flow

1. Dashboard
   - Highlight the live summary cards, market overview sparklines, latest signals, pipeline status, and monitoring status.
   - Point out that the home page combines trading and MLOps health in one screen.
2. Market Explorer
   - Show recent OHLCV data and explain that everything downstream starts with the market ingest layer.
3. Strategy Lab
   - Open feature stats and label distributions to show the engineered dataset quality.
4. Training Lab
   - Walk through experiment history, best model metrics, and feature importance.
5. Model Registry
   - Explain champion versus challenger promotion workflow and audit logging.
6. Backtesting Center
   - Show equity curve, drawdown, trade log, and benchmark comparison.
7. Signal Center
   - Highlight latest BUY / SELL / HOLD predictions and per-ticker history.
8. Paper Portfolio
   - Show live portfolio value, open positions, order history, alerts, and watchlist management.
9. Monitoring Center
   - Explain drift detection, prediction drift, rolling F1, freshness, and manual retraining.
10. Admin Settings and Help / Docs
   - Show configuration persistence and the embedded documentation hub.

## Expected Highlights

- Dashboard loads with real data from the backend.
- Portfolio summary and order log are populated.
- Monitoring shows drift and health severity.
- Tests pass and the stack is Dockerized.
- Deployment docs exist for Vercel, Render, Supabase, and local Docker.

## Talking Points By Page

- Dashboard: one-screen control center for product and platform health.
- Research pages: explainability starts with visible raw market and feature data.
- ML pages: experiments are tracked and models are governed, not just trained once.
- Trading pages: backtest, signal generation, and paper execution form a believable workflow.
- Ops pages: production monitoring and retraining are part of the product story, not an afterthought.
