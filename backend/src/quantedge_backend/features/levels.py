"""Swing levels, window extremes, and classic pivot."""

from __future__ import annotations

from typing import Any, cast

import numpy as np


def session_window_extremes(high: np.ndarray, low: np.ndarray) -> tuple[float, float]:
    """Max high and min low over the full series (rolling 'session' window)."""
    return float(np.max(high)), float(np.min(low))


def classic_pivot(high: float, low: float, close: float) -> tuple[float, float, float]:
    """Classic pivot from H/L/C (typically prior period; here last bar)."""
    p = (high + low + close) / 3.0
    r1 = 2 * p - low
    s1 = 2 * p - high
    return p, r1, s1


def find_swings(
    high: np.ndarray,
    low: np.ndarray,
    *,
    lookback: int = 2,
) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Local swing highs and lows using a centered window."""
    n = len(high)
    swing_highs: list[tuple[int, float]] = []
    swing_lows: list[tuple[int, float]] = []
    for i in range(lookback, n - lookback):
        window_h = high[i - lookback : i + lookback + 1]
        window_l = low[i - lookback : i + lookback + 1]
        if float(high[i]) >= float(np.max(window_h)):
            swing_highs.append((i, float(high[i])))
        if float(low[i]) <= float(np.min(window_l)):
            swing_lows.append((i, float(low[i])))
    return swing_highs, swing_lows


def levels_from_swings_and_pivot(
    *,
    last_close: float,
    last_high: float,
    last_low: float,
    swing_highs: list[tuple[int, float]],
    swing_lows: list[tuple[int, float]],
    max_swings: int = 3,
) -> list[dict[str, float | str | None]]:
    """Structured support/resistance/pivot levels for ``market-features`` schema."""
    levels: list[dict[str, float | str | None]] = []
    p, r1, s1 = classic_pivot(last_high, last_low, last_close)
    levels.append(
        {"price": p, "kind": "pivot", "strength": 0.55, "label": "classic_pivot"},
    )
    levels.append(
        {"price": r1, "kind": "resistance", "strength": 0.45, "label": "r1"},
    )
    levels.append(
        {"price": s1, "kind": "support", "strength": 0.45, "label": "s1"},
    )

    highs_sorted = sorted(swing_highs, key=lambda t: t[1])
    lows_sorted = sorted(swing_lows, key=lambda t: t[1])
    for _, price in highs_sorted[-max_swings:]:
        kind: str = "resistance" if price >= last_close else "other"
        levels.append(
            {
                "price": price,
                "kind": kind,
                "strength": 0.4,
                "label": "swing_high",
            },
        )
    for _, price in lows_sorted[:max_swings]:
        kind = "support" if price <= last_close else "other"
        levels.append(
            {
                "price": price,
                "kind": kind,
                "strength": 0.4,
                "label": "swing_low",
            },
        )
    return levels


def dedupe_levels(
    levels: list[dict[str, float | str | None]],
    *,
    price_tol: float,
) -> list[dict[str, float | str | None]]:
    """Merge levels within ``price_tol`` (keep higher strength)."""
    if not levels:
        return []
    sorted_lv = sorted(levels, key=lambda x: float(cast(Any, x["price"])))
    out: list[dict[str, float | str | None]] = []
    for lv in sorted_lv:
        p = float(cast(Any, lv["price"]))
        if not out:
            out.append(lv)
            continue
        last = out[-1]
        if abs(p - float(cast(Any, last["price"]))) <= price_tol:
            s_new = float(cast(Any, lv.get("strength") or 0))
            s_old = float(cast(Any, last.get("strength") or 0))
            if s_new > s_old:
                out[-1] = lv
        else:
            out.append(lv)
    return out
