# API Reference

Swagger and ReDoc are available from the running backend:

- `/docs`
- `/redoc`

## Market

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| GET | `/api/market/tickers` | none | `TickerInfo[]` |
| GET | `/api/market/ohlcv/{ticker}` | query: `start_date`, `end_date`, `limit` | `OHLCVRow[]` |
| GET | `/api/market/latest/{ticker}` | none | `OHLCVRow` |
| GET | `/api/market/stats/{ticker}` | none | `TickerStats` |
| GET | `/api/market/freshness` | none | `FreshnessReport` |
| POST | `/api/market/ingest` | `{ tickers?: string[] }` | `IngestResponse` |

## Features and Dataset

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| GET | `/api/features/list/{ticker}` | query: `limit` | `FeatureListResponse` |
| GET | `/api/features/stats/{ticker}` | none | `FeatureStatsResponse` |
| POST | `/api/features/run` | `{ tickers?, split_date?, build_dataset }` | `PipelineRunResponse` |
| GET | `/api/labels/distribution` | none | `LabelDistribution[]` |
| GET | `/api/labels/distribution/{ticker}` | none | `LabelDistribution` |
| GET | `/api/dataset/versions` | none | `DatasetVersionInfo[]` |
| GET | `/api/dataset/{version}/summary` | none | `DatasetVersionInfo` |

## Training, Experiments, Registry

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| POST | `/api/training/run` | `StartTrainingRequest` | `StartTrainingResponse` |
| GET | `/api/training/status/{job_id}` | none | `TrainingJobStatus` |
| GET | `/api/experiments/list` | query: `limit` | `ExperimentRun[]` |
| GET | `/api/experiments/best` | none | `ExperimentRun \| null` |
| GET | `/api/experiments/{run_id}` | none | `RunDetails` |
| GET | `/api/models/registry` | none | `RegisteredModel[]` |
| GET | `/api/models/{model_name}/versions` | none | `ModelVersion[]` |
| GET | `/api/models/{run_id}/importance` | none | `FeatureImportances` |
| GET | `/api/registry/models` | none | `RegisteredModelInfo[]` |
| GET | `/api/registry/models/{model_name}/champion` | none | `ModelVersionInfo` |
| GET | `/api/registry/models/{model_name}/challengers` | none | `ModelVersionInfo[]` |
| GET | `/api/registry/models/{model_name}/versions` | none | `ModelVersionInfo[]` |
| GET | `/api/registry/models/{model_name}/compare` | none | `ComparisonResult` |
| POST | `/api/registry/models/{model_name}/promote` | `PromoteRequest` | object |
| POST | `/api/registry/models/{model_name}/archive` | `ArchiveRequest` | object |
| POST | `/api/registry/models/{model_name}/auto-promote` | none | `AutoPromoteResult` |
| GET | `/api/registry/log` | query: `limit` | `RegistryLogEntry[]` |

## Backtesting

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| POST | `/api/backtest/run` | `StartBacktestRequest` | `StartBacktestResponse` |
| GET | `/api/backtest/status/{job_id}` | none | `BacktestJobStatus` |
| GET | `/api/backtest/runs` | query: `limit` | `BacktestSummary[]` |
| GET | `/api/backtest/{run_id}` | none | `BacktestDetail` |
| GET | `/api/backtest/{run_id}/equity` | none | `EquityPoint[]` |
| GET | `/api/backtest/{run_id}/drawdown` | none | `DrawdownPoint[]` |
| GET | `/api/backtest/{run_id}/trades` | none | `BacktestTrade[]` |
| GET | `/api/backtest/compare` | query: `run_ids` | `BacktestSummary[]` |

## Signals

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| POST | `/api/signals/run` | `RunInferenceRequest` | `StartInferenceResponse` |
| GET | `/api/signals/status/{job_id}` | none | `InferenceJobStatus` |
| GET | `/api/signals/latest` | query: `signal` | `LatestSignal[]` |
| GET | `/api/signals/history/{ticker}` | query: `limit` | `SignalHistoryPoint[]` |
| GET | `/api/signals/ticker/{ticker}/latest` | none | `LatestSignal` |
| GET | `/api/signals/{signal_id}` | none | `SignalOut` |

## Monitoring

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| GET | `/api/monitoring/latest` | none | `MonitoringSummary` |
| GET | `/api/monitoring/history` | query: `days` | `MonitoringHistoryItem[]` |
| GET | `/api/monitoring/drift/data` | none | `DataDriftSummary` |
| GET | `/api/monitoring/drift/features` | none | `FeatureDriftDetail[]` |
| GET | `/api/monitoring/drift/predictions` | none | `PredictionDriftReport` |
| GET | `/api/monitoring/performance` | none | `PerformanceReport` |
| GET | `/api/monitoring/freshness` | none | `FreshnessReport` |
| GET | `/api/monitoring/alerts` | none | `MonitoringAlert[]` |
| POST | `/api/monitoring/retrain` | `ManualRetrainRequest` | `ManualRetrainResponse` |
| GET | `/api/monitoring/retrain/history` | query: `limit` | `RetrainHistoryItem[]` |

## Portfolio, Alerts, Watchlist

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| GET | `/api/portfolio/summary` | none | `PortfolioSummary` |
| GET | `/api/portfolio/positions` | none | `PositionOut[]` |
| GET | `/api/portfolio/positions/{ticker}` | none | `PositionDetail` |
| GET | `/api/portfolio/orders` | query: `limit`, `offset`, `order_type`, `ticker` | `OrdersResponse` |
| GET | `/api/portfolio/history` | query: `days` | `PortfolioHistoryPoint[]` |
| GET | `/api/portfolio/pnl` | none | `PnLBreakdown` |
| GET | `/api/alerts/` | query: `limit`, `offset`, `severity`, `unread_only` | `AlertListResponse` |
| GET | `/api/alerts/unread` | none | `{ unread: number }` |
| POST | `/api/alerts/{id}/read` | none | `{ success, updated }` |
| POST | `/api/alerts/read-all` | none | `{ success, updated }` |
| GET | `/api/watchlist/` | none | `WatchlistItemOut[]` |
| POST | `/api/watchlist/add` | `AddWatchlistRequest` | `WatchlistMutationResponse` |
| DELETE | `/api/watchlist/{ticker}` | none | `WatchlistMutationResponse` |

## Dashboard, Settings, System

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| GET | `/api/dashboard/overview` | none | `DashboardOverview` |
| GET | `/api/settings` | none | `AppSettingsResponse` |
| POST | `/api/settings` | partial `AppSettingsResponse` sections | `AppSettingsResponse` |
| GET | `/api/system/status` | none | system status object |

## Schema Notes

- Most date fields are ISO `YYYY-MM-DD`.
- Most timestamps are ISO 8601 UTC strings.
- Numeric fields are serialized as JSON numbers, even when sourced from SQL numeric columns.
- Empty or unavailable model outputs are returned as `null` instead of placeholder strings.
