#!/usr/bin/env sh
set -eu

cd /app

python -c "from mlops.flows.ingest_flow import market_data_ingest_flow; market_data_ingest_flow(only_stale=False)"
python -c "from mlops.flows.feature_flow import feature_engineering_pipeline; feature_engineering_pipeline()"
python -c "from mlops.flows.inference_flow import daily_inference_flow; daily_inference_flow()"
