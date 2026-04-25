import { getPublicApiBaseUrl, getServerApiBaseUrl } from "@/lib/env";

const API_BASE = typeof window !== "undefined" ? getPublicApiBaseUrl() : getServerApiBaseUrl();

// ---------------------------------------------------------------------------
// Types (mirrors backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface OHLCVRow {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  adj_close: number | null;
  volume: number | null;
}

export interface TickerInfo {
  ticker: string;
  name: string;
  sector: string;
  last_date: string | null;
  last_close: number | null;
  volume: number | null;
  freshness: "fresh" | "stale" | "missing";
  change_pct: number | null;
}

export interface TickerStats {
  ticker: string;
  current_price: number | null;
  week52_high: number | null;
  week52_low: number | null;
  avg_volume: number | null;
  ytd_return: number | null;
  data_from: string | null;
  data_to: string | null;
}

export interface FreshnessInfo {
  ticker: string;
  status: "fresh" | "stale" | "missing";
  last_date: string | null;
  days_stale: number | null;
}

export interface FreshnessReport {
  tickers: Record<string, FreshnessInfo>;
  checked_at: string;
}

export interface IngestResponse {
  message: string;
  tickers_ingested: string[];
  tickers_failed: string[];
  rows_added: number;
}

// ---------------------------------------------------------------------------
// Fetch helpers — auto-unwrap { data, meta } envelope
// ---------------------------------------------------------------------------

interface ApiEnvelope<T> {
  data: T;
  meta: { timestamp: string; version: string };
}

interface ApiError {
  error: { code: number; message: string; details: unknown };
}

async function unwrap<T>(res: Response, label: string): Promise<T> {
  if (!res.ok) {
    let msg = `${label} → ${res.status} ${res.statusText}`;
    try {
      const err = (await res.json()) as ApiError;
      if (err?.error?.message) msg = err.error.message;
    } catch {}
    throw new Error(msg);
  }
  const envelope = (await res.json()) as ApiEnvelope<T>;
  return envelope.data;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  return unwrap<T>(res, `GET ${path}`);
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  return unwrap<T>(res, `POST ${path}`);
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    cache: "no-store",
  });
  return unwrap<T>(res, `DELETE ${path}`);
}

// ---------------------------------------------------------------------------
// Feature engineering types
// ---------------------------------------------------------------------------

export interface FeatureRow {
  date: string;
  close?: number | null;
  // Trend
  sma_10?: number | null;  sma_20?: number | null;
  sma_50?: number | null;  sma_200?: number | null;
  ema_10?: number | null;  ema_20?: number | null;  ema_50?: number | null;
  macd_line?: number | null;  macd_signal?: number | null;  macd_hist?: number | null;
  adx_14?: number | null;
  price_vs_sma20_pct?: number | null;  price_vs_sma50_pct?: number | null;
  // Momentum
  rsi_14?: number | null;  stoch_k?: number | null;  stoch_d?: number | null;
  roc_10?: number | null;  williams_r?: number | null;
  // Volatility
  bb_upper?: number | null;  bb_lower?: number | null;
  bb_width?: number | null;  bb_pct_b?: number | null;
  atr_14?: number | null;    hist_vol_20?: number | null;
  // Volume
  obv?: number | null;  vol_sma_20?: number | null;
  vol_ratio?: number | null;  cmf_20?: number | null;
  // Price action
  daily_return?: number | null;  return_3d?: number | null;
  return_5d?: number | null;     return_10d?: number | null;
  gap_pct?: number | null;       hl_range_pct?: number | null;
  candle_body_pct?: number | null;
}

export interface FeatureListResponse {
  ticker: string;
  count:  number;
  rows:   FeatureRow[];
}

export interface FeatureStat {
  mean:     number | null;
  std:      number | null;
  min:      number | null;
  max:      number | null;
  null_pct: number | null;
}

export interface FeatureStatsResponse {
  ticker:     string;
  total_rows: number;
  stats:      Record<string, FeatureStat>;
}

export interface LabelDistribution {
  ticker: string;
  total:  number;
  BUY:    number;
  SELL:   number;
  HOLD:   number;
}

export interface DatasetVersion {
  version:           number;
  tickers:           string[];
  date_range_start:  string | null;
  date_range_end:    string | null;
  n_rows:            number | null;
  n_train:           number | null;
  n_test:            number | null;
  feature_list:      string[];
  label_distribution: { BUY: number; SELL: number; HOLD: number };
  split_date:        string | null;
  file_path:         string | null;
  created_at:        string | null;
}

export interface PipelineRunResponse {
  message:             string;
  tickers_processed:   string[];
  tickers_skipped:     string[];
  dataset_version:     number | null;
  label_distribution:  { BUY: number; SELL: number; HOLD: number } | null;
}

// ---------------------------------------------------------------------------
// Market API
// ---------------------------------------------------------------------------

export const marketApi = {
  getTickers: () => get<TickerInfo[]>("/api/market/tickers"),

  getOHLCV: (
    ticker: string,
    startDate?: string,
    endDate?: string,
    limit?: number
  ) => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    if (limit) params.set("limit", String(limit));
    const qs = params.toString();
    return get<OHLCVRow[]>(`/api/market/ohlcv/${ticker}${qs ? `?${qs}` : ""}`);
  },

  getLatest: (ticker: string) => get<OHLCVRow>(`/api/market/latest/${ticker}`),

  getStats: (ticker: string) => get<TickerStats>(`/api/market/stats/${ticker}`),

  getFreshness: () => get<FreshnessReport>("/api/market/freshness"),

  triggerIngest: (tickers?: string[]) =>
    post<IngestResponse>("/api/market/ingest", tickers ? { tickers } : {}),
};

// ---------------------------------------------------------------------------
// Features API
// ---------------------------------------------------------------------------

export const featuresApi = {
  getList: (ticker: string, limit = 30) =>
    get<FeatureListResponse>(`/api/features/list/${ticker}?limit=${limit}`),

  getStats: (ticker: string) =>
    get<FeatureStatsResponse>(`/api/features/stats/${ticker}`),

  runPipeline: (body?: { tickers?: string[]; split_date?: string; build_dataset?: boolean }) =>
    post<PipelineRunResponse>("/api/features/run", body ?? {}),

  getLabelDistributions: () =>
    get<LabelDistribution[]>("/api/labels/distribution"),
};

// ---------------------------------------------------------------------------
// Dataset API
// ---------------------------------------------------------------------------

export const datasetApi = {
  getVersions: () =>
    get<DatasetVersion[]>("/api/dataset/versions"),

  getSummary: (version: number) =>
    get<DatasetVersion>(`/api/dataset/${version}/summary`),
};

// ---------------------------------------------------------------------------
// Training types
// ---------------------------------------------------------------------------

export interface ExperimentRun {
  run_id:          string;
  run_name:        string;
  model_name:      string;
  status:          string;
  start_time:      string | null;
  end_time:        string | null;
  duration_s:      number | null;
  dataset_version: number | null;
  train_size:      number | null;
  test_size:       number | null;
  accuracy:        number | null;
  precision_macro: number | null;
  recall_macro:    number | null;
  f1_macro:        number | null;
  roc_auc:         number | null;
}

export interface ConfusionMatrix {
  matrix: number[][];
  labels: string[];
}

export interface RunDetails {
  run_id:                string;
  run_name:              string;
  model_name:            string;
  status:                string;
  start_time:            string | null;
  end_time:              string | null;
  duration_s:            number | null;
  params:                Record<string, string>;
  metrics:               Record<string, number>;
  confusion_matrix:      ConfusionMatrix | null;
  classification_report: Record<string, Record<string, number>> | null;
  dataset_version:       number | null;
  train_size:            number | null;
  test_size:             number | null;
}

export interface FeatureImportanceItem {
  feature: string;
  score:   number;
}

export interface FeatureImportances {
  run_id:      string;
  model_name:  string;
  importances: FeatureImportanceItem[];
}

export interface RegisteredModel {
  name:              string;
  latest_version:    string | null;
  stage:             string | null;
  best_model_name:   string | null;
  description:       string | null;
  creation_time:     string | null;
  last_updated_time: string | null;
}

export interface ModelVersion {
  version:       string;
  stage:         string;
  run_id:        string | null;
  creation_time: string | null;
  description:   string | null;
  status:        string | null;
}

export interface StartTrainingRequest {
  dataset_version:  number;
  model_list?:      string[] | null;
  run_name:         string;
  n_optuna_trials:  number;
}

export interface TrainingJobStatus {
  job_id:  string;
  status:  "running" | "complete" | "failed";
  message: string;
  result?: Record<string, unknown> | null;
  error?:  string | null;
}

export interface StartTrainingResponse {
  job_id:  string;
  message: string;
}

// ---------------------------------------------------------------------------
// Training API
// ---------------------------------------------------------------------------

export const trainingApi = {
  startTraining: (body: StartTrainingRequest) =>
    post<StartTrainingResponse>("/api/training/run", body),

  getStatus: (jobId: string) =>
    get<TrainingJobStatus>(`/api/training/status/${jobId}`),
};

// ---------------------------------------------------------------------------
// Experiments API
// ---------------------------------------------------------------------------

export const experimentsApi = {
  list: (limit = 100) =>
    get<ExperimentRun[]>(`/api/experiments/list?limit=${limit}`),

  getBest: () =>
    get<ExperimentRun | null>("/api/experiments/best"),

  getDetails: (runId: string) =>
    get<RunDetails>(`/api/experiments/${runId}`),
};

// ---------------------------------------------------------------------------
// Models API
// ---------------------------------------------------------------------------

export const modelsApi = {
  getRegistry: () =>
    get<RegisteredModel[]>("/api/models/registry"),

  getVersions: (modelName: string) =>
    get<ModelVersion[]>(`/api/models/${modelName}/versions`),

  getImportance: (runId: string) =>
    get<FeatureImportances>(`/api/models/${runId}/importance`),
};

// ---------------------------------------------------------------------------
// Backtest types
// ---------------------------------------------------------------------------

export interface StartBacktestRequest {
  model_run_id?:    string | null;
  tickers:          string[];
  start_date:       string;
  end_date:         string;
  initial_capital:  number;
  transaction_cost: number;
  slippage:         number;
  position_frac:    number;
  strategy_name?:   string | null;
}

export interface StartBacktestResponse {
  job_id:  string;
  message: string;
}

export interface BacktestJobStatus {
  job_id:  string;
  status:  "running" | "complete" | "failed";
  message: string;
  run_ids: string[];
  error?:  string | null;
}

export interface BacktestSummary {
  run_id:            string;
  batch_id:          string | null;
  ticker:            string;
  strategy_name:     string | null;
  model_run_id:      string | null;
  start_date:        string | null;
  end_date:          string | null;
  initial_capital:   number | null;
  total_return:      number | null;
  annualized_return: number | null;
  benchmark_return:  number | null;
  alpha:             number | null;
  max_drawdown:      number | null;
  sharpe_ratio:      number | null;
  sortino_ratio:     number | null;
  calmar_ratio:      number | null;
  daily_volatility:  number | null;
  total_trades:      number | null;
  win_rate:          number | null;
  avg_win:           number | null;
  avg_loss:          number | null;
  profit_factor:     number | null;
  avg_holding_days:  number | null;
  created_at:        string | null;
}

export interface EquityPoint {
  date:      string;
  value:     number;
  benchmark: number | null;
}

export interface DrawdownPoint {
  date:     string;
  drawdown: number;
}

export interface BacktestTrade {
  entry_date:   string;
  exit_date:    string;
  entry_price:  number;
  exit_price:   number;
  shares:       number;
  pnl:          number;
  return_pct:   number;
  holding_days: number;
}

export interface BacktestDetail extends BacktestSummary {
  transaction_cost:  number | null;
  slippage:          number | null;
  position_frac:     number | null;
  equity_curve:      EquityPoint[];
  drawdown:          DrawdownPoint[];
  trades:            BacktestTrade[];
  monthly_returns:   Record<string, number>;
}

// ---------------------------------------------------------------------------
// Backtest API
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Signal types
// ---------------------------------------------------------------------------

export interface LatestSignal {
  ticker:        string;
  signal_date:   string | null;
  signal:        string | null;
  confidence:    number | null;
  prob_buy:      number | null;
  prob_sell:     number | null;
  prob_hold:     number | null;
  model_version: string | null;
  explanation:   string | null;
}

export interface SignalHistoryPoint {
  signal_date: string;
  signal:      string;
  confidence:  number | null;
  close:       number | null;
}

export interface SignalOut {
  id:            number;
  ticker:        string;
  signal_date:   string;
  signal:        string;
  confidence:    number | null;
  prob_buy:      number | null;
  prob_sell:     number | null;
  prob_hold:     number | null;
  model_version: string | null;
  model_run_id:  string | null;
  explanation:   string | null;
  created_at:    string | null;
}

export interface RunInferenceRequest {
  tickers?:              string[] | null;
  confidence_threshold?: number;
  feature_limit?:        number;
}

export interface StartInferenceResponse {
  job_id:  string;
  message: string;
}

export interface InferenceJobStatus {
  job_id:         string;
  status:         "running" | "complete" | "failed";
  message:        string;
  total_signals:  number | null;
  model_run_id:   string | null;
  model_version:  string | null;
  error:          string | null;
}

// ---------------------------------------------------------------------------
// Registry types
// ---------------------------------------------------------------------------

export interface ModelVersionInfo {
  version:       string;
  stage:         string;
  run_id:        string | null;
  f1_macro:      number | null;
  accuracy:      number | null;
  roc_auc:       number | null;
  model_name:    string | null;
  creation_time: number | null;
  description:   string | null;
  status:        string | null;
}

export interface RegisteredModelInfo {
  name:              string;
  latest_version:    string | null;
  stage:             string | null;
  description:       string | null;
  creation_time:     number | null;
  last_updated_time: number | null;
  tags:              Record<string, string> | null;
}

export interface ComparisonResult {
  model_name:   string;
  champion:     ModelVersionInfo | null;
  challengers:  ModelVersionInfo[];
}

export interface PromoteRequest {
  version:     string;
  notes:       string;
  promoted_by: string;
}

export interface AutoPromoteResult {
  promoted:     boolean;
  old_champion: ModelVersionInfo | null;
  new_champion: ModelVersionInfo | null;
  message:      string;
}

export interface RegistryLogEntry {
  id:            number;
  model_name:    string;
  version:       string;
  stage:         string;
  f1_score:      number | null;
  promoted_at:   string | null;
  promoted_by:   string | null;
  notes:         string | null;
  mlflow_run_id: string | null;
  created_at:    string | null;
}

// ---------------------------------------------------------------------------
// Signal API
// ---------------------------------------------------------------------------

export const signalsApi = {
  runInference: (body: RunInferenceRequest) =>
    post<StartInferenceResponse>("/api/signals/run", body),

  getStatus: (jobId: string) =>
    get<InferenceJobStatus>(`/api/signals/status/${jobId}`),

  getLatest: (signal?: string) => {
    const qs = signal ? `?signal=${signal}` : "";
    return get<LatestSignal[]>(`/api/signals/latest${qs}`);
  },

  getHistory: (ticker: string, limit = 90) =>
    get<SignalHistoryPoint[]>(`/api/signals/history/${ticker}?limit=${limit}`),

  getTickerLatest: (ticker: string) =>
    get<LatestSignal>(`/api/signals/ticker/${ticker}/latest`),

  getById: (id: number) =>
    get<SignalOut>(`/api/signals/${id}`),
};

// ---------------------------------------------------------------------------
// Registry API
// ---------------------------------------------------------------------------

export const registryApi = {
  listModels: () =>
    get<RegisteredModelInfo[]>("/api/registry/models"),

  getChampion: (modelName: string) =>
    get<ModelVersionInfo>(`/api/registry/models/${modelName}/champion`),

  getChallengers: (modelName: string) =>
    get<ModelVersionInfo[]>(`/api/registry/models/${modelName}/challengers`),

  listVersions: (modelName: string) =>
    get<ModelVersionInfo[]>(`/api/registry/models/${modelName}/versions`),

  compare: (modelName: string) =>
    get<ComparisonResult>(`/api/registry/models/${modelName}/compare`),

  promote: (modelName: string, body: PromoteRequest) =>
    post<Record<string, unknown>>(`/api/registry/models/${modelName}/promote`, body),

  archive: (modelName: string, version: string) =>
    post<Record<string, unknown>>(`/api/registry/models/${modelName}/archive`, { version }),

  autoPromote: (modelName: string) =>
    post<AutoPromoteResult>(`/api/registry/models/${modelName}/auto-promote`),

  getLog: (limit = 50) =>
    get<RegistryLogEntry[]>(`/api/registry/log?limit=${limit}`),
};

// ---------------------------------------------------------------------------
// Backtest API
// ---------------------------------------------------------------------------

export const backtestApi = {
  run: (body: StartBacktestRequest) =>
    post<StartBacktestResponse>("/api/backtest/run", body),

  getStatus: (jobId: string) =>
    get<BacktestJobStatus>(`/api/backtest/status/${jobId}`),

  listRuns: (limit = 200) =>
    get<BacktestSummary[]>(`/api/backtest/runs?limit=${limit}`),

  getDetail: (runId: string) =>
    get<BacktestDetail>(`/api/backtest/${runId}`),

  getEquity: (runId: string) =>
    get<EquityPoint[]>(`/api/backtest/${runId}/equity`),

  getDrawdown: (runId: string) =>
    get<DrawdownPoint[]>(`/api/backtest/${runId}/drawdown`),

  getTrades: (runId: string) =>
    get<BacktestTrade[]>(`/api/backtest/${runId}/trades`),

  compare: (runIds: string[]) =>
    get<BacktestSummary[]>(`/api/backtest/compare?run_ids=${runIds.join(",")}`),
};

// ---------------------------------------------------------------------------
// Monitoring types
// ---------------------------------------------------------------------------

export type AlertSeverity = "INFO" | "WARN" | "CRITICAL";
export type SystemHealth = "HEALTHY" | "WARNING" | "CRITICAL";

export interface MonitoringAlert {
  id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  timestamp: string;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  reference_density: number;
  current_density: number;
}

export interface FeatureDriftDetail {
  feature: string;
  drift_detected: boolean;
  drift_score: number;
  p_value: number | null;
  reference_mean: number | null;
  current_mean: number | null;
  reference_std: number | null;
  current_std: number | null;
  reference_count: number;
  current_count: number;
  histogram: HistogramBin[];
}

export interface DataDriftSummary {
  drift_share: number;
  drifted_count: number;
  feature_count: number;
  summary_text: string;
  top_drifted: FeatureDriftDetail[];
}

export interface PredictionDriftReport {
  detected: boolean;
  threshold: number;
  reference_counts: Record<string, number>;
  current_counts: Record<string, number>;
  reference_ratios: Record<string, number>;
  current_ratios: Record<string, number>;
  ratio_shifts: Record<string, number>;
  largest_ratio_shift: number;
  reference_total: number;
  current_total: number;
}

export interface RollingPerformancePoint {
  date: string;
  f1: number;
  accuracy: number;
  sample_size: number;
}

export interface MonitoringPerformanceReport {
  ground_truth_available: boolean;
  window_days: number;
  baseline_f1: number | null;
  baseline_accuracy: number | null;
  baseline_source: string | null;
  last_training_at: string | null;
  current_f1: number | null;
  current_accuracy: number | null;
  degradation_pct: number | null;
  degradation_detected: boolean;
  sample_size: number;
  rolling: RollingPerformancePoint[];
}

export interface FreshnessTickerStatus {
  ticker: string;
  last_market_date: string | null;
  last_ingested_at: string | null;
  days_stale: number | null;
  status: "fresh" | "stale";
}

export interface MonitoringFreshnessReport {
  checked_at: string;
  stale_threshold_days: number;
  stale_count: number;
  ticker_count: number;
  tickers: FreshnessTickerStatus[];
}

export interface MonitoringSummary {
  id: number | null;
  report_date: string | null;
  report_type: string | null;
  drift_share: number | null;
  prediction_drift_detected: boolean;
  model_perf_f1: number | null;
  alert_level: AlertSeverity;
  system_status: SystemHealth;
  feature_count: number;
  drifted_count: number;
  active_alerts: number;
  evidently_report_html: string | null;
  created_at: string | null;
  last_retrain_at: string | null;
  last_retrain_reason: string | null;
}

export interface MonitoringHistoryItem {
  id: number;
  report_date: string;
  report_type: string;
  drift_share: number | null;
  prediction_drift_detected: boolean;
  model_perf_f1: number | null;
  alert_level: AlertSeverity;
  created_at: string | null;
}

export interface ManualRetrainRequest {
  reason?: string;
}

export interface ManualRetrainResponse {
  triggered: boolean;
  reasons: string[];
  metrics: Record<string, number | string | null>;
  workflow: Record<string, unknown> | null;
  log_id: number | null;
  old_model_version?: string | null;
  new_model_version?: string | null;
  new_f1?: number | null;
  promoted?: boolean | null;
  notes?: string | null;
}

export interface RetrainHistoryItem {
  id: number;
  triggered_at: string;
  trigger_reason: string;
  old_model_version: string | null;
  new_model_version: string | null;
  new_f1: number | null;
  promoted: boolean;
  notes: string | null;
  created_at: string | null;
}

// ---------------------------------------------------------------------------
// Monitoring API
// ---------------------------------------------------------------------------

export const monitoringApi = {
  getLatest: () => get<MonitoringSummary>("/api/monitoring/latest"),

  getHistory: (days = 30) =>
    get<MonitoringHistoryItem[]>(`/api/monitoring/history?days=${days}`),

  getDataDrift: () =>
    get<DataDriftSummary>("/api/monitoring/drift/data"),

  getFeatureDrift: () =>
    get<FeatureDriftDetail[]>("/api/monitoring/drift/features"),

  getPredictionDrift: () =>
    get<PredictionDriftReport>("/api/monitoring/drift/predictions"),

  getPerformance: () =>
    get<MonitoringPerformanceReport>("/api/monitoring/performance"),

  getFreshness: () =>
    get<MonitoringFreshnessReport>("/api/monitoring/freshness"),

  getAlerts: () =>
    get<MonitoringAlert[]>("/api/monitoring/alerts"),

  triggerRetrain: (body?: ManualRetrainRequest) =>
    post<ManualRetrainResponse>("/api/monitoring/retrain", body ?? {}),

  getRetrainHistory: (limit = 50) =>
    get<RetrainHistoryItem[]>(`/api/monitoring/retrain/history?limit=${limit}`),
};

// ---------------------------------------------------------------------------
// Portfolio types
// ---------------------------------------------------------------------------

export interface PositionHighlight {
  ticker: string;
  company_name: string | null;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface PortfolioSummary {
  snapshot_date: string | null;
  total_value: number;
  daily_change: number;
  daily_change_pct: number;
  total_pnl: number;
  total_pnl_pct: number;
  realized_pnl: number;
  unrealized_pnl: number;
  cash_balance: number;
  invested_value: number;
  open_positions: number;
  initial_capital: number;
  best_position: PositionHighlight | null;
  worst_position: PositionHighlight | null;
}

export interface PositionOut {
  id: number;
  ticker: string;
  entry_date: string;
  entry_price: number;
  shares: number;
  current_price: number | null;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  status: "OPEN" | "CLOSED";
  company_name: string | null;
  sector: string | null;
  created_at: string | null;
}

export interface OrderOut {
  id: number;
  ticker: string;
  order_date: string;
  order_type: "BUY" | "SELL";
  price: number;
  shares: number;
  total_value: number;
  transaction_cost: number;
  signal_id: number | null;
  created_at: string | null;
}

export interface PositionDetail {
  position: PositionOut;
  orders: OrderOut[];
}

export interface OrdersResponse {
  total: number;
  items: OrderOut[];
}

export interface PortfolioHistoryPoint {
  snapshot_date: string;
  total_value: number;
  cash_balance: number;
  invested_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

export interface PnLBreakdown {
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  total_pnl_pct: number;
  best_position: PositionHighlight | null;
  worst_position: PositionHighlight | null;
}

// ---------------------------------------------------------------------------
// Alerts and watchlist types
// ---------------------------------------------------------------------------

export interface AppAlert {
  id: number;
  alert_type: string;
  ticker: string | null;
  message: string;
  severity: AlertSeverity;
  is_read: boolean;
  created_at: string | null;
}

export interface AlertListResponse {
  total: number;
  items: AppAlert[];
}

export interface WatchlistItem {
  id: number;
  ticker: string;
  company_name: string;
  sector: string | null;
  added_at: string | null;
  is_active: boolean;
}

export interface WatchlistMutationResponse {
  success: boolean;
  ticker: string;
  pipeline_status: string | null;
  message: string;
}

// ---------------------------------------------------------------------------
// Settings and dashboard types
// ---------------------------------------------------------------------------

export interface ModelSettings {
  signal_threshold: number;
  confidence_filter: number;
  position_sizing_pct: number;
}

export interface BacktestDefaults {
  initial_capital: number;
  transaction_cost: number;
  slippage: number;
}

export interface RetrainSettings {
  auto_retrain_enabled: boolean;
  drift_threshold: number;
  performance_threshold: number;
}

export interface PortfolioEngineSettings {
  initial_cash: number;
  max_positions: number;
  transaction_cost: number;
}

export interface EnvironmentStatus {
  database_ok: boolean;
  mlflow_ok: boolean;
  scheduler_running: boolean;
  prefect_available: boolean;
  last_pipeline_runs: Record<string, unknown>;
}

export interface SystemInfo {
  app_version: string;
  python_version: string;
  model_version: string | null;
  dataset_version: number | null;
}

export interface AppSettings {
  model: ModelSettings;
  backtest: BacktestDefaults;
  retrain: RetrainSettings;
  portfolio: PortfolioEngineSettings;
  environment: EnvironmentStatus;
  system: SystemInfo;
}

export interface SparklinePoint {
  date: string;
  close: number;
}

export interface WatchlistSparkline {
  ticker: string;
  company_name: string;
  current_price: number | null;
  change_pct: number | null;
  points: SparklinePoint[];
}

export interface DashboardSignalItem {
  ticker: string;
  signal: string;
  confidence: number | null;
  signal_date: string | null;
  created_at: string | null;
}

export interface DashboardAlertItem {
  id: number;
  severity: string;
  message: string;
  ticker: string | null;
  created_at: string | null;
}

export interface PipelineStatusItem {
  key: string;
  label: string;
  status: "healthy" | "warning" | "critical" | "idle";
  last_run_at: string | null;
  last_status: string | null;
  description: string;
}

export interface DashboardModelPerformance {
  champion_model_name: string | null;
  champion_model_version: string | null;
  champion_f1: number | null;
  current_f1: number | null;
  days_since_last_training: number | null;
}

export interface DashboardOverview {
  portfolio: PortfolioSummary;
  signals_today: Record<string, number>;
  open_positions_count: number;
  monitoring_status: string;
  market_overview: WatchlistSparkline[];
  latest_signals: DashboardSignalItem[];
  portfolio_history: PortfolioHistoryPoint[];
  recent_alerts: DashboardAlertItem[];
  pipeline_status: PipelineStatusItem[];
  model_performance: DashboardModelPerformance;
}

// ---------------------------------------------------------------------------
// Portfolio API
// ---------------------------------------------------------------------------

export const portfolioApi = {
  getSummary: () => get<PortfolioSummary>("/api/portfolio/summary"),

  getPositions: () => get<PositionOut[]>("/api/portfolio/positions"),

  getPositionDetail: (ticker: string) =>
    get<PositionDetail>(`/api/portfolio/positions/${ticker}`),

  getOrders: (params?: { limit?: number; offset?: number; order_type?: string; ticker?: string }) => {
    const search = new URLSearchParams();
    if (params?.limit) search.set("limit", String(params.limit));
    if (params?.offset) search.set("offset", String(params.offset));
    if (params?.order_type) search.set("order_type", params.order_type);
    if (params?.ticker) search.set("ticker", params.ticker);
    const qs = search.toString();
    return get<OrdersResponse>(`/api/portfolio/orders${qs ? `?${qs}` : ""}`);
  },

  getHistory: (days?: number) =>
    get<PortfolioHistoryPoint[]>(`/api/portfolio/history${days ? `?days=${days}` : ""}`),

  getPnl: () => get<PnLBreakdown>("/api/portfolio/pnl"),
};

// ---------------------------------------------------------------------------
// Alerts API
// ---------------------------------------------------------------------------

export const alertsApi = {
  list: (params?: { limit?: number; offset?: number; severity?: string; unread_only?: boolean }) => {
    const search = new URLSearchParams();
    if (params?.limit) search.set("limit", String(params.limit));
    if (params?.offset) search.set("offset", String(params.offset));
    if (params?.severity) search.set("severity", params.severity);
    if (params?.unread_only) search.set("unread_only", "true");
    const qs = search.toString();
    return get<AlertListResponse>(`/api/alerts/${qs ? `?${qs}` : ""}`);
  },

  unread: () => get<{ unread: number }>("/api/alerts/unread"),

  markRead: (id: number) => post<{ success: boolean; updated: number }>(`/api/alerts/${id}/read`),

  markAllRead: () => post<{ success: boolean; updated: number }>("/api/alerts/read-all"),
};

// ---------------------------------------------------------------------------
// Watchlist API
// ---------------------------------------------------------------------------

export const watchlistApi = {
  list: () => get<WatchlistItem[]>("/api/watchlist/"),

  add: (body: { ticker: string; company_name?: string; sector?: string }) =>
    post<WatchlistMutationResponse>("/api/watchlist/add", body),

  remove: (ticker: string) =>
    del<WatchlistMutationResponse>(`/api/watchlist/${ticker}`),
};

// ---------------------------------------------------------------------------
// Settings API
// ---------------------------------------------------------------------------

export const settingsApi = {
  get: () => get<AppSettings>("/api/settings"),

  save: (body: Partial<AppSettings>) => post<AppSettings>("/api/settings", body),
};

// ---------------------------------------------------------------------------
// Dashboard API
// ---------------------------------------------------------------------------

export const dashboardApi = {
  overview: () => get<DashboardOverview>("/api/dashboard/overview"),
};
