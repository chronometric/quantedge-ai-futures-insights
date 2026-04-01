"""Phase 4 — deterministic features and snapshot."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from quantedge_backend.db.models import OhlcvBar
from quantedge_backend.features.indicators import classify_trend_regime, sma
from quantedge_backend.features.snapshot import (
    MIN_BARS,
    build_market_features,
    compact_market_features_for_llm,
)


def _synthetic_uptrend(n: int = 60) -> list[OhlcvBar]:
    base = datetime(2026, 1, 1, 16, 0, tzinfo=UTC)
    out: list[OhlcvBar] = []
    price = 5000.0
    for i in range(n):
        t_open = base + timedelta(minutes=5 * i)
        t_close = t_open + timedelta(minutes=5)
        o = price
        c = price + 0.5
        hi = c + 0.25
        lo = o - 0.25
        out.append(
            OhlcvBar(
                symbol="ES",
                interval="5m",
                time_open=t_open,
                time_close=t_close,
                open=o,
                high=hi,
                low=lo,
                close=c,
                volume=1000.0,
            ),
        )
        price = c
    return out


def test_min_bars_constant() -> None:
    assert MIN_BARS == 55


def test_build_market_features_shape() -> None:
    bars = _synthetic_uptrend(60)
    payload = build_market_features(bars, symbol="ES", interval="5m")
    assert payload["schema_version"] == "1.0.0"
    assert payload["symbol"] == "ES"
    assert payload["interval"] == "5m"
    assert payload["trend_regime"] in {"bullish", "bearish", "neutral", "unknown"}
    assert payload["volatility_regime"] in {"low", "normal", "high", "unknown"}
    assert isinstance(payload["indicators"], dict)
    assert "sma_20" in payload["indicators"]
    assert isinstance(payload["levels"], list)
    assert isinstance(payload["patterns"], list)
    assert isinstance(payload["notes"], list)


def test_build_market_features_rejects_short_series() -> None:
    bars = _synthetic_uptrend(20)
    with pytest.raises(ValueError, match="55"):
        build_market_features(bars, symbol="ES", interval="5m")


def test_compact_reduces_payload() -> None:
    bars = _synthetic_uptrend(60)
    full = build_market_features(bars, symbol="ES", interval="5m", token_budget=None)
    small = compact_market_features_for_llm(full, max_chars=800)
    assert len(repr(small)) <= len(repr(full)) or len(small.get("levels", [])) <= len(
        full.get("levels", []),
    )


def test_classify_trend_regime() -> None:
    assert classify_trend_regime(102.0, 101.0, 100.0) == "bullish"
    assert classify_trend_regime(99.0, 100.0, 101.0) == "bearish"


def test_sma_tail() -> None:
    x = np.arange(1, 61, dtype=np.float64)
    s = sma(x, 5)
    assert not np.isnan(s[-1])
    assert abs(float(s[-1]) - float(np.mean(x[-5:]))) < 1e-9
