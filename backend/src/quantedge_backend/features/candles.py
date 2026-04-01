"""OHLCV series helpers for numpy-based indicators."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from quantedge_backend.db.models import OhlcvBar


def bars_to_arrays(
    bars: Sequence[OhlcvBar],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (open, high, low, close, volume) as float64 arrays in bar order."""
    n = len(bars)
    o = np.empty(n, dtype=np.float64)
    h = np.empty(n, dtype=np.float64)
    lo = np.empty(n, dtype=np.float64)
    c = np.empty(n, dtype=np.float64)
    v = np.empty(n, dtype=np.float64)
    for i, b in enumerate(bars):
        o[i] = b.open
        h[i] = b.high
        lo[i] = b.low
        c[i] = b.close
        v[i] = b.volume
    return o, h, lo, c, v
