#!/usr/bin/env sh
set -eu

export PREFECT_API_URL="${PREFECT_API_URL:-http://prefect:4200/api}"
cd /app

prefect config set PREFECT_API_URL="$PREFECT_API_URL"

prefect deployment build mlops/flows/ingest_flow.py:market_data_ingest_flow \
  --name "daily-ingest" \
  --cron "${INGEST_CRON:-15 22 * * 1-5}" \
  --apply

prefect deployment build mlops/flows/feature_flow.py:feature_engineering_pipeline \
  --name "daily-features" \
  --cron "${FEATURE_CRON:-30 22 * * 1-5}" \
  --apply

prefect deployment build mlops/flows/inference_flow.py:daily_inference_flow \
  --name "daily-inference" \
  --cron "${INFERENCE_CRON:-45 22 * * 1-5}" \
  --apply

prefect deployment build mlops/flows/monitoring_flow.py:daily_monitoring_flow \
  --name "daily-monitoring" \
  --cron "${MONITORING_CRON:-0 23 * * 1-5}" \
  --apply

prefect agent start -q default
