export const FEATURE_GROUPS = {
  trend: [
    "sma_10", "sma_20", "sma_50", "sma_200",
    "ema_10", "ema_20", "ema_50",
    "macd_line", "macd_signal", "macd_hist", "adx_14",
    "price_vs_sma20_pct", "price_vs_sma50_pct",
  ],
  momentum:  ["rsi_14", "stoch_k", "stoch_d", "roc_10", "williams_r"],
  volatility: ["bb_upper", "bb_lower", "bb_width", "bb_pct_b", "atr_14", "hist_vol_20"],
  volume:    ["obv", "vol_sma_20", "vol_ratio", "cmf_20"],
  price_action: [
    "daily_return", "return_3d", "return_5d", "return_10d",
    "gap_pct", "hl_range_pct", "candle_body_pct",
  ],
} as const;

export type FeatureGroup = keyof typeof FEATURE_GROUPS;

export const ALL_FEATURES: string[] = Object.values(FEATURE_GROUPS).flat();

export const GROUP_LABELS: Record<FeatureGroup, string> = {
  trend:        "Trend",
  momentum:     "Momentum",
  volatility:   "Volatility",
  volume:       "Volume",
  price_action: "Price Action",
};

export const GROUP_COLORS: Record<FeatureGroup, string> = {
  trend:        "#f97316",   // orange
  momentum:     "#a855f7",   // purple
  volatility:   "#64748b",   // slate
  volume:       "#3b82f6",   // blue
  price_action: "#10b981",   // emerald
};

/** Human-readable label for a feature key */
export function featureLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Sma/g, "SMA")
    .replace(/Ema/g, "EMA")
    .replace(/Macd/g, "MACD")
    .replace(/Rsi/g, "RSI")
    .replace(/Adx/g, "ADX")
    .replace(/Atr/g, "ATR")
    .replace(/Bb/g, "BB")
    .replace(/Obv/g, "OBV")
    .replace(/Cmf/g, "CMF")
    .replace(/Pct/g, "%")
    .replace(/Vs/g, "vs");
}
