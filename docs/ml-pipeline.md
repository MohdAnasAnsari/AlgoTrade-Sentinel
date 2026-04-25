# ML Pipeline

## Feature Engineering

Feature generation lives in `ml/features/feature_engineer.py` and produces 35 indicators grouped into five categories.

### Trend

- `sma_10`, `sma_20`, `sma_50`, `sma_200`: simple moving averages over common lookback windows.
- `ema_10`, `ema_20`, `ema_50`: exponential moving averages with faster weighting on recent prices.
- `macd_line`, `macd_signal`, `macd_hist`: MACD momentum trend trio.
- `adx_14`: average directional index for trend strength.
- `price_vs_sma20_pct`, `price_vs_sma50_pct`: percent distance from the moving average baseline.

### Momentum

- `rsi_14`: 14-period RSI.
- `stoch_k`, `stoch_d`: stochastic oscillator fast and smoothed values.
- `roc_10`: 10-period rate of change.
- `williams_r`: Williams %R over the rolling high/low range.

### Volatility

- `bb_upper`, `bb_lower`: Bollinger Band bounds.
- `bb_width`: band width as a percent of price level.
- `bb_pct_b`: relative location within the Bollinger Band envelope.
- `atr_14`: average true range.
- `hist_vol_20`: annualized 20-day historical volatility from log returns.

### Volume

- `obv`: on-balance volume.
- `vol_sma_20`: 20-day average volume.
- `vol_ratio`: current volume divided by average volume.
- `cmf_20`: Chaikin money flow.

### Price Action

- `daily_return`: one-day return.
- `return_3d`, `return_5d`, `return_10d`: short-horizon returns.
- `gap_pct`: open versus prior close gap.
- `hl_range_pct`: intraday high-low range as a percent of close.
- `candle_body_pct`: absolute candle body size as a percent of close.

## Label Logic

Label generation lives in `ml/features/label_builder.py`.

- Lookahead horizon: 5 trading days.
- `future_return_5d = (future_close - close) / close`
- Default labels:
  - `BUY` if future return > `+2%`
  - `SELL` if future return < `-2%`
  - `HOLD` otherwise
- Final lookahead rows with no forward data are marked `null` and dropped for training.

## Dataset Building

`ml/features/dataset_builder.py` merges features and labels, writes versioned parquet artifacts into `ml/artifacts/datasets/`, and stores metadata in `dataset_versions`.

Stored metadata includes:

- dataset version
- tickers used
- date range
- train/test split date
- feature list
- label distribution
- row counts for total, train, and test splits

## Training Process

Training lives under `ml/training/`.

Workflow:

1. Load a versioned dataset.
2. Split train and test partitions using the configured split date.
3. Tune candidate models with Optuna.
4. Log parameters, metrics, confusion matrix entries, and feature importances to MLflow.
5. Register the best candidate in MLflow Model Registry.
6. Promote or compare candidates through the registry workflow.

Tracked metrics include:

- accuracy
- precision macro
- recall macro
- F1 macro
- ROC AUC where applicable
- confusion matrix cells
- per-class report metrics
- feature importance values when supported by the estimator

## Inference

Inference loads recent engineered feature rows per ticker and applies the champion model to produce:

- predicted class: `BUY`, `SELL`, or `HOLD`
- class probabilities
- model version and run ID
- optional explanation metadata

If live signal rows are not available yet, the UI can fall back to labelled data so the product remains demo-friendly.

## Monitoring

Monitoring compares:

- reference data: latest training dataset artifact
- current data: rolling feature window, default 30 days

Checks include:

- feature distribution drift
- prediction mix drift
- current performance versus baseline F1
- data freshness by ticker
- retraining triggers and audit logs

## Backtesting Methodology

Backtesting uses the pure engine in `ml/backtesting/backtest_engine.py`.

Core assumptions:

- event-driven BUY / SELL / HOLD signals
- position entry on price with slippage and transaction cost
- benchmark comparison against SPY if available, otherwise ticker buy-and-hold
- full equity curve and drawdown tracking

Reported metrics:

- total return
- annualized return
- benchmark return
- alpha
- max drawdown
- Sharpe ratio
- Sortino ratio
- Calmar ratio
- daily volatility
- trade count
- win rate
- average win and loss
- profit factor
- average holding days

## Paper Portfolio

The paper portfolio engine simulates a simple production-like execution model:

- configurable initial cash
- next-session execution for BUY / SELL signals
- equal-weight capital allocation
- max concurrent positions
- transaction cost per trade
- daily snapshots for total value, cash, invested capital, realized PnL, and unrealized PnL
