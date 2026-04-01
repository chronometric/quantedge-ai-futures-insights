"""Unit tests for 1m → 5m aggregation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantedge_backend.market.aggregate import FiveMinuteAggregator, align_one_minute_bar_open
from quantedge_backend.market.types import OneMinuteBar


def _m(
    t: datetime,
    o: float,
    h: float,
    lo: float,
    c: float,
    v: float,
) -> OneMinuteBar:
    return OneMinuteBar(
        time_open=t,
        time_close=t + timedelta(minutes=1),
        open=o,
        high=h,
        low=lo,
        close=c,
        volume=v,
    )


def test_align_one_minute_bar_open_normalizes_to_minute_boundary() -> None:
    t = datetime(2026, 4, 1, 14, 7, 23, tzinfo=UTC)
    b = _m(t, 1, 2, 0.5, 1.5, 100)
    a = align_one_minute_bar_open(b)
    assert a.time_open == datetime(2026, 4, 1, 14, 7, tzinfo=UTC)
    assert a.time_close == datetime(2026, 4, 1, 14, 8, tzinfo=UTC)


def test_five_minute_aggregator_completes_after_bucket_change() -> None:
    base = datetime(2026, 4, 1, 14, 0, tzinfo=UTC)
    agg = FiveMinuteAggregator()
    done, _ = agg.add(_m(base, 10, 11, 9, 10.5, 100))
    assert done is None
    done, _ = agg.add(_m(base + timedelta(minutes=1), 10.5, 12, 10, 11, 120))
    assert done is None
    done, _ = agg.add(_m(base + timedelta(minutes=2), 11, 13, 10.5, 12, 130))
    assert done is None
    done, _ = agg.add(_m(base + timedelta(minutes=3), 12, 14, 11, 13, 140))
    assert done is None
    done, w = agg.add(_m(base + timedelta(minutes=4), 13, 15, 12, 14, 150))
    assert done is None
    assert not w
    done, _ = agg.add(_m(base + timedelta(minutes=5), 14, 16, 13, 15, 160))
    assert done is not None
    assert done.time_open == base
    assert done.time_close == base + timedelta(minutes=5)
    assert done.open == 10
    assert done.close == 14
    assert done.volume == 100 + 120 + 130 + 140 + 150
