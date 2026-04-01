"""Market data value types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OneMinuteBar:
    """Single 1m OHLCV bar (UTC)."""

    time_open: datetime
    time_close: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True, slots=True)
class FiveMinuteBar:
    """Aggregated 5m bar ready for persistence (UTC)."""

    time_open: datetime
    time_close: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
