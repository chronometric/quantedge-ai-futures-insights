"""Aggregate 1-minute bars into 5-minute OHLCV."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from quantedge_backend.market.time_bucketing import (
    ceil_5m_close_utc,
    ensure_utc,
    floor_5m_open_utc,
    floor_minute_utc,
)
from quantedge_backend.market.types import FiveMinuteBar, OneMinuteBar

logger = logging.getLogger(__name__)

_ONE_MINUTE = timedelta(minutes=1)


@dataclass(slots=True)
class FiveMinuteAggregator:
    """Stateful 5m builder for one symbol."""

    _bucket_open: datetime | None = None
    _open: float = 0.0
    _high: float = 0.0
    _low: float = 0.0
    _close: float = 0.0
    _volume: float = 0.0
    _last_minute_open: datetime | None = None

    def add(self, bar: OneMinuteBar) -> tuple[FiveMinuteBar | None, list[str]]:
        """Return a completed 5m bar (if any) and gap warnings."""
        warnings: list[str] = []
        o = ensure_utc(bar.time_open)
        bucket = floor_5m_open_utc(o)

        if self._last_minute_open is not None:
            expected = self._last_minute_open + _ONE_MINUTE
            if o > expected:
                warnings.append(
                    f"gap: expected next 1m at {expected.isoformat()}, got {o.isoformat()}",
                )
                for w in warnings:
                    logger.info("%s", w)
        self._last_minute_open = o

        if self._bucket_open is None:
            self._start_bucket(bucket, bar)
            return None, warnings

        if bucket != self._bucket_open:
            finished = self._finalize_bucket()
            self._start_bucket(bucket, bar)
            return finished, warnings

        self._merge(bar)
        return None, warnings

    def _start_bucket(self, bucket_open: datetime, bar: OneMinuteBar) -> None:
        self._bucket_open = bucket_open
        self._open = bar.open
        self._high = bar.high
        self._low = bar.low
        self._close = bar.close
        self._volume = bar.volume

    def _merge(self, bar: OneMinuteBar) -> None:
        self._high = max(self._high, bar.high)
        self._low = min(self._low, bar.low)
        self._close = bar.close
        self._volume += bar.volume

    def _finalize_bucket(self) -> FiveMinuteBar:
        assert self._bucket_open is not None
        bucket_open = self._bucket_open
        close_time = ceil_5m_close_utc(bucket_open)
        return FiveMinuteBar(
            time_open=bucket_open,
            time_close=close_time,
            open=self._open,
            high=self._high,
            low=self._low,
            close=self._close,
            volume=self._volume,
        )

    def flush_open(self) -> FiveMinuteBar | None:
        """Emit incomplete bucket (e.g. shutdown)."""
        if self._bucket_open is None:
            return None
        return self._finalize_bucket()


def align_one_minute_bar_open(bar: OneMinuteBar) -> OneMinuteBar:
    """Normalize timestamps to minute boundaries (UTC)."""
    o = floor_minute_utc(bar.time_open)
    c = o + _ONE_MINUTE
    return OneMinuteBar(
        time_open=o,
        time_close=c,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
    )
