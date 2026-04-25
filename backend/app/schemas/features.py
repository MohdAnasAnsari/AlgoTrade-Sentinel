from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Feature row (single date)
# ---------------------------------------------------------------------------

class FeatureRow(BaseModel):
    date: str
    close: float | None = None
    # Trend
    sma_10:  float | None = None
    sma_20:  float | None = None
    sma_50:  float | None = None
    sma_200: float | None = None
    ema_10:  float | None = None
    ema_20:  float | None = None
    ema_50:  float | None = None
    macd_line:   float | None = None
    macd_signal: float | None = None
    macd_hist:   float | None = None
    adx_14:      float | None = None
    price_vs_sma20_pct: float | None = None
    price_vs_sma50_pct: float | None = None
    # Momentum
    rsi_14:    float | None = None
    stoch_k:   float | None = None
    stoch_d:   float | None = None
    roc_10:    float | None = None
    williams_r: float | None = None
    # Volatility
    bb_upper:    float | None = None
    bb_lower:    float | None = None
    bb_width:    float | None = None
    bb_pct_b:    float | None = None
    atr_14:      float | None = None
    hist_vol_20: float | None = None
    # Volume
    obv:        int   | None = None
    vol_sma_20: float | None = None
    vol_ratio:  float | None = None
    cmf_20:     float | None = None
    # Price action
    daily_return:    float | None = None
    return_3d:       float | None = None
    return_5d:       float | None = None
    return_10d:      float | None = None
    gap_pct:         float | None = None
    hl_range_pct:    float | None = None
    candle_body_pct: float | None = None

    model_config = {"from_attributes": True}


class FeatureListResponse(BaseModel):
    ticker: str
    count:  int
    rows:   list[FeatureRow]


# ---------------------------------------------------------------------------
# Feature statistics
# ---------------------------------------------------------------------------

class FeatureStat(BaseModel):
    mean:     float | None
    std:      float | None
    min:      float | None
    max:      float | None
    null_pct: float | None


class FeatureStatsResponse(BaseModel):
    ticker:     str
    total_rows: int
    stats:      dict[str, FeatureStat]


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

class LabelDistribution(BaseModel):
    ticker: str
    total:  int
    BUY:    int
    SELL:   int
    HOLD:   int


# ---------------------------------------------------------------------------
# Dataset versions
# ---------------------------------------------------------------------------

class DatasetVersionInfo(BaseModel):
    version:          int
    tickers:          list[str]
    date_range_start: str | None
    date_range_end:   str | None
    n_rows:           int | None
    n_train:          int | None
    n_test:           int | None
    feature_list:     list[str]
    label_distribution: dict[str, int]
    split_date:       str | None
    file_path:        str | None
    created_at:       str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class PipelineRunRequest(BaseModel):
    tickers:     list[str] | None = None
    split_date:  str | None       = None
    build_dataset: bool           = True


class PipelineRunResponse(BaseModel):
    message:            str
    tickers_processed:  list[str]
    tickers_skipped:    list[str]
    dataset_version:    int | None
    label_distribution: dict[str, int] | None
