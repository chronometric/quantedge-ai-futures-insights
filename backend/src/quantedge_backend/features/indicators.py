"""Moving averages, ATR, returns, and regime labels."""

from __future__ import annotations

import math

import numpy as np


def sma(values: np.ndarray, period: int) -> np.ndarray:
    """Simple moving average; leading values are nan until ``period`` samples exist."""
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or n < period:
        return out
    c = np.cumsum(values, dtype=np.float64)
    out[period - 1] = c[period - 1] / period
    for i in range(period, n):
        out[i] = (c[i] - c[i - period]) / period
    return out


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """True range per bar; index 0 uses high-low only."""
    n = len(high)
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    return tr


def atr_wilder(tr: np.ndarray, period: int) -> np.ndarray:
    """Wilder ATR; leading values nan until stabilized."""
    n = len(tr)
    out = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or n < period:
        return out
    first = float(np.mean(tr[:period]))
    out[period - 1] = first
    for i in range(period, n):
        prev = out[i - 1]
        if math.isnan(prev):
            break
        out[i] = (prev * (period - 1) + tr[i]) / period
    return out


def log_returns(close: np.ndarray) -> np.ndarray:
    """Log returns; first element is nan."""
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    for i in range(1, n):
        if close[i - 1] > 0 and close[i] > 0:
            out[i] = math.log(close[i] / close[i - 1])
    return out


def realized_volatility(log_ret: np.ndarray, window: int) -> float:
    """Std dev of log returns over last ``window`` non-nan values (sample std)."""
    tail = log_ret[-window:]
    xs = tail[~np.isnan(tail)]
    if len(xs) < 2:
        return float("nan")
    return float(np.std(xs, ddof=1))


def classify_trend_regime(close: float, sma_fast: float, sma_slow: float) -> str:
    """Bullish / bearish / neutral from MA stack vs price."""
    if math.isnan(close) or math.isnan(sma_fast) or math.isnan(sma_slow):
        return "unknown"
    if close > sma_fast > sma_slow:
        return "bullish"
    if close < sma_fast < sma_slow:
        return "bearish"
    return "neutral"


def classify_volatility_regime(atr_pct: float, history_atr_pct: np.ndarray) -> str:
    """
    Low / normal / high from current ATR% vs distribution of ATR% in window.
    Uses 33rd / 66th percentiles of valid history values.
    """
    if math.isnan(atr_pct):
        return "unknown"
    xs = history_atr_pct[~np.isnan(history_atr_pct)]
    if len(xs) < 5:
        return "unknown"
    p33 = float(np.percentile(xs, 33))
    p66 = float(np.percentile(xs, 66))
    if atr_pct < p33:
        return "low"
    if atr_pct > p66:
        return "high"
    return "normal"
