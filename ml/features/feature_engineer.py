"""
Feature engineering: 35 technical indicators from OHLCV data.

Input:  DataFrame with columns [ticker, date, open, high, low, close, adj_close, volume]
        Sorted ascending by date, single ticker.
Output: DataFrame with [ticker, date, close] + ALL_FEATURES columns.
"""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Feature catalogue
# ---------------------------------------------------------------------------

FEATURE_GROUPS: dict[str, list[str]] = {
    "trend": [
        "sma_10", "sma_20", "sma_50", "sma_200",
        "ema_10", "ema_20", "ema_50",
        "macd_line", "macd_signal", "macd_hist", "adx_14",
        "price_vs_sma20_pct", "price_vs_sma50_pct",
    ],
    "momentum": ["rsi_14", "stoch_k", "stoch_d", "roc_10", "williams_r"],
    "volatility": ["bb_upper", "bb_lower", "bb_width", "bb_pct_b", "atr_14", "hist_vol_20"],
    "volume": ["obv", "vol_sma_20", "vol_ratio", "cmf_20"],
    "price_action": [
        "daily_return", "return_3d", "return_5d", "return_10d",
        "gap_pct", "hl_range_pct", "candle_body_pct",
    ],
}

ALL_FEATURES: list[str] = [f for group in FEATURE_GROUPS.values() for f in group]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all 35 technical features for a single ticker's OHLCV DataFrame.
    Returns DataFrame with [ticker, date, close] + ALL_FEATURES.
    NaN values arise naturally from indicator warm-up periods.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)

    c = df["close"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    o = df["open"].astype(float)
    v = df["volume"].astype(float).fillna(0.0)

    # ── TREND ─────────────────────────────────────────────────────────────
    df["sma_10"]  = c.rolling(10).mean()
    df["sma_20"]  = c.rolling(20).mean()
    df["sma_50"]  = c.rolling(50).mean()
    df["sma_200"] = c.rolling(200).mean()

    df["ema_10"] = c.ewm(span=10, adjust=False).mean()
    df["ema_20"] = c.ewm(span=20, adjust=False).mean()
    df["ema_50"] = c.ewm(span=50, adjust=False).mean()

    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd_line"]   = ema12 - ema26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_hist"]   = df["macd_line"] - df["macd_signal"]

    df["adx_14"] = _adx(h, l, c, 14)

    df["price_vs_sma20_pct"] = (c - df["sma_20"]) / df["sma_20"] * 100
    df["price_vs_sma50_pct"] = (c - df["sma_50"]) / df["sma_50"] * 100

    # ── MOMENTUM ──────────────────────────────────────────────────────────
    df["rsi_14"] = _rsi(c, 14)
    df["stoch_k"], df["stoch_d"] = _stochastic(h, l, c, 14, 3)
    df["roc_10"] = (c - c.shift(10)) / c.shift(10) * 100

    hi14 = h.rolling(14).max()
    lo14 = l.rolling(14).min()
    df["williams_r"] = (hi14 - c) / (hi14 - lo14).replace(0.0, np.nan) * (-100.0)

    # ── VOLATILITY ────────────────────────────────────────────────────────
    sma20 = df["sma_20"]
    std20 = c.rolling(20).std(ddof=0)
    df["bb_upper"] = sma20 + 2.0 * std20
    df["bb_lower"] = sma20 - 2.0 * std20
    bb_range = (df["bb_upper"] - df["bb_lower"]).replace(0.0, np.nan)
    df["bb_width"] = bb_range / sma20 * 100.0
    df["bb_pct_b"] = (c - df["bb_lower"]) / bb_range

    df["atr_14"] = _atr(h, l, c, 14)

    log_ret = np.log(c / c.shift(1))
    df["hist_vol_20"] = log_ret.rolling(20).std() * np.sqrt(252) * 100.0

    # ── VOLUME ────────────────────────────────────────────────────────────
    obv_dir = np.sign(c.diff().fillna(0.0))
    df["obv"] = (v * obv_dir).cumsum()
    df["vol_sma_20"] = v.rolling(20).mean()
    df["vol_ratio"]  = v / df["vol_sma_20"].replace(0.0, np.nan)

    clv = ((c - l) - (h - c)) / (h - l).replace(0.0, np.nan)
    df["cmf_20"] = (clv * v).rolling(20).sum() / v.rolling(20).sum().replace(0.0, np.nan)

    # ── PRICE ACTION ─────────────────────────────────────────────────────
    df["daily_return"]    = c.pct_change() * 100.0
    df["return_3d"]       = c.pct_change(3) * 100.0
    df["return_5d"]       = c.pct_change(5) * 100.0
    df["return_10d"]      = c.pct_change(10) * 100.0
    df["gap_pct"]         = (o - c.shift(1)) / c.shift(1) * 100.0
    df["hl_range_pct"]    = (h - l) / c * 100.0
    df["candle_body_pct"] = (c - o).abs() / c * 100.0

    return df[["ticker", "date", "close"] + ALL_FEATURES]


# ---------------------------------------------------------------------------
# Private indicator helpers
# ---------------------------------------------------------------------------

def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0.0)
    loss     = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _stochastic(
    high: pd.Series, low: pd.Series, close: pd.Series,
    k_period: int = 14, d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    lo_k  = low.rolling(k_period).min()
    hi_k  = high.rolling(k_period).max()
    rng   = (hi_k - lo_k).replace(0.0, np.nan)
    k     = (close - lo_k) / rng * 100.0
    d     = k.rolling(d_period).mean()
    return k, d


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    prev = close.shift(1)
    tr   = pd.concat(
        [high - low, (high - prev).abs(), (low - prev).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)
    prev_close = close.shift(1)

    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    up   = high - prev_high
    down = prev_low - low

    pos_dm = np.where((up > down) & (up > 0.0), up, 0.0)
    neg_dm = np.where((down > up) & (down > 0.0), down, 0.0)

    alpha    = 1.0 / period
    pos_di_s = pd.Series(pos_dm, index=close.index).ewm(alpha=alpha, adjust=False).mean()
    neg_di_s = pd.Series(neg_dm, index=close.index).ewm(alpha=alpha, adjust=False).mean()
    tr_s     = tr.ewm(alpha=alpha, adjust=False).mean().replace(0.0, np.nan)

    pos_di  = pos_di_s / tr_s * 100.0
    neg_di  = neg_di_s / tr_s * 100.0
    di_sum  = (pos_di + neg_di).replace(0.0, np.nan)
    dx      = (pos_di - neg_di).abs() / di_sum * 100.0
    return dx.ewm(alpha=alpha, adjust=False).mean()
