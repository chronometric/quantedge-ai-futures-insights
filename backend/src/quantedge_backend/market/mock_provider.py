"""Synthetic 1m bar stream for development (no external API)."""

from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from quantedge_backend.market.time_bucketing import floor_minute_utc
from quantedge_backend.market.types import OneMinuteBar


async def mock_one_minute_stream(
    symbols: list[str],
    *,
    tick_seconds: float,
    seed: int = 42,
) -> AsyncIterator[tuple[str, OneMinuteBar]]:
    """
    Emit aligned 1m bars for all symbols, then advance the clock by one minute.

    Wall-clock delay between steps is ``tick_seconds`` (fast-forward for demos).
    """
    rng = random.Random(seed)
    prices: dict[str, float] = {s: 5000.0 + rng.random() * 40.0 for s in symbols}
    t = floor_minute_utc(datetime.now(UTC))
    while True:
        for sym in symbols:
            o = prices[sym]
            delta = rng.uniform(-2.0, 2.0)
            c = max(0.01, o + delta)
            hi = max(o, c) + rng.uniform(0.0, 1.0)
            lo = min(o, c) - rng.uniform(0.0, 1.0)
            vol = rng.uniform(100.0, 2000.0)
            bar = OneMinuteBar(
                time_open=t,
                time_close=t + timedelta(minutes=1),
                open=o,
                high=hi,
                low=lo,
                close=c,
                volume=vol,
            )
            yield sym, bar
            prices[sym] = c
        t += timedelta(minutes=1)
        await asyncio.sleep(tick_seconds)
