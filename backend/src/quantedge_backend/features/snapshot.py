"""Build ``market-features`` JSON from OHLCV bars (deterministic, token-aware)."""

from __future__ import annotations

import copy
import math
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import numpy as np

from quantedge_backend.db.models import OhlcvBar
from quantedge_backend.features.candles import bars_to_arrays
from quantedge_backend.features.indicators import (
    atr_wilder,
    classify_trend_regime,
    classify_volatility_regime,
    log_returns,
    realized_volatility,
    sma,
    true_range,
)
from quantedge_backend.features.levels import (
    dedupe_levels,
    find_swings,
    levels_from_swings_and_pivot,
    session_window_extremes,
)

MIN_BARS = 55
ATR_PERIOD = 14
SMA_FAST = 20
SMA_SLOW = 50
RV_WINDOW = 20
DEFAULT_MAX_LEVELS = 12
DEFAULT_MAX_NOTES = 6


def build_market_features(
    bars: Sequence[OhlcvBar],
    *,
    symbol: str,
    interval: str,
    token_budget: int | None = None,
) -> dict[str, Any]:
    """
    Deterministic pipeline: bars → structured context for RAG/LLM and UI.

    ``token_budget`` (optional) applies a coarse shrink via
    :func:`compact_market_features_for_llm` (estimated ~4 chars per token).
    """
    if len(bars) < MIN_BARS:
        msg = f"need at least {MIN_BARS} bars, got {len(bars)}"
        raise ValueError(msg)
    _o, h, lo, c, _v = bars_to_arrays(bars)
    last = bars[-1]
    last_close = float(last.close)
    last_high = float(last.high)
    last_low = float(last.low)
    as_of: datetime = last.time_close

    tr = true_range(h, lo, c)
    atr = atr_wilder(tr, ATR_PERIOD)
    sma_f = sma(c, SMA_FAST)
    sma_s = sma(c, SMA_SLOW)
    lr = log_returns(c)

    i = len(c) - 1
    atr_last = float(atr[i])
    sma20 = float(sma_f[i])
    sma50 = float(sma_s[i])
    atr_pct = (atr_last / last_close * 100.0) if last_close > 0 else float("nan")
    atr_pct_hist = np.where(np.isnan(atr), np.nan, atr / c * 100.0)

    trend = classify_trend_regime(last_close, sma20, sma50)
    vol = classify_volatility_regime(atr_pct, atr_pct_hist)

    sess_hi, sess_lo = session_window_extremes(h, lo)
    sess_range_pct = ((sess_hi - sess_lo) / last_close * 100.0) if last_close > 0 else float("nan")

    ret1 = float(lr[i]) if not math.isnan(lr[i]) else float("nan")
    ret5 = float(np.nansum(lr[max(0, i - 4) : i + 1]))
    rv20 = realized_volatility(lr, RV_WINDOW)

    swing_highs, swing_lows = find_swings(h, lo, lookback=2)
    raw_levels = levels_from_swings_and_pivot(
        last_close=last_close,
        last_high=last_high,
        last_low=last_low,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
        max_swings=3,
    )
    tol = max(1e-4 * last_close, 0.25 * atr_last) if not math.isnan(atr_last) else 1e-4 * last_close
    levels = dedupe_levels(raw_levels, price_tol=tol)[:DEFAULT_MAX_LEVELS]

    indicators: dict[str, Any] = {
        "sma_20": sma20,
        "sma_50": sma50,
        "atr_14": atr_last,
        "atr_pct": atr_pct,
        "ret_1_bar_log": ret1,
        "ret_5_bar_log": ret5,
        "realized_vol_log_20": rv20,
        "session_high": sess_hi,
        "session_low": sess_lo,
        "session_range_pct": sess_range_pct,
    }

    patterns: list[str] = []
    if trend == "bullish":
        patterns.append("ma_stack_bullish")
    elif trend == "bearish":
        patterns.append("ma_stack_bearish")
    if vol == "low":
        patterns.append("compressed_range")
    if (
        not math.isnan(sess_range_pct)
        and not math.isnan(atr_pct)
        and atr_pct > 0
        and sess_range_pct < atr_pct * 3
    ):
        patterns.append("tight_session_vs_atr")

    notes = [
        f"window_bars={len(bars)} interval={interval}",
        f"session_high={sess_hi:.6g} session_low={sess_lo:.6g}",
    ]

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "symbol": symbol.upper(),
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "interval": interval,
        "trend_regime": trend,
        "volatility_regime": vol,
        "indicators": indicators,
        "levels": levels,
        "patterns": patterns,
        "notes": notes[:DEFAULT_MAX_NOTES],
    }

    if token_budget is not None:
        est_chars = max(256, int(token_budget * 4))
        return compact_market_features_for_llm(payload, max_chars=est_chars)
    return payload


def compact_market_features_for_llm(
    payload: dict[str, Any],
    *,
    max_chars: int,
) -> dict[str, Any]:
    """
    Shrink a market-features dict to roughly fit ``max_chars`` (coarse budget for LLM context).

    Preserves required keys; trims indicators, levels, patterns, and notes.
    """
    out = copy.deepcopy(payload)
    ind = out.get("indicators")
    if isinstance(ind, dict):
        keys = list(ind.keys())[:16]
        out["indicators"] = {k: ind[k] for k in keys}

    levels = out.get("levels")
    if isinstance(levels, list):
        out["levels"] = levels[:8]

    pats = out.get("patterns")
    if isinstance(pats, list):
        out["patterns"] = [str(x)[:64] for x in pats[:6]]

    notes = out.get("notes")
    if isinstance(notes, list):
        joined = " | ".join(str(x) for x in notes)
        if len(joined) > max_chars // 4:
            joined = joined[: max_chars // 4] + "…"
        out["notes"] = [joined]

    # Hard cap serialized size (best-effort)
    def approx_size(obj: Any) -> int:
        return len(repr(obj))

    while approx_size(out) > max_chars and isinstance(out.get("levels"), list) and out["levels"]:
        out["levels"] = out["levels"][:-1]
        if not out["levels"]:
            break

    return out
