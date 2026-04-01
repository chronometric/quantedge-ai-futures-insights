"""Mock insight path (no OpenAI)."""

from __future__ import annotations

from quantedge_backend.llm.insight_service import build_mock_insight


def test_build_mock_insight_minimal() -> None:
    features = {
        "trend_regime": "bullish",
        "volatility_regime": "normal",
        "levels": [{"price": 5000.0, "kind": "resistance", "strength": 0.8}],
    }
    out = build_mock_insight(
        symbol="ES",
        interval="5m",
        market_features=features,
        chunk_ids=["methodology_risk_01"],
        kb_version="1.0.0",
    )
    assert out["schema_version"] == "1.0.0"
    assert out["structured"]["bias"] == "bullish"
    assert out["retrieval"]["chunk_ids"] == ["methodology_risk_01"]
    assert "disclaimer" in out
