"""Insight payload Pydantic models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quantedge_backend.llm.schemas import (
    LlmInsightPartial,
    Narrative,
    RetrievalBlock,
    StructuredInsight,
    insight_payload_to_dict,
)


def test_insight_payload_serialization() -> None:
    partial = LlmInsightPartial(
        structured=StructuredInsight(
            bias="neutral",
            key_levels=[],
            scenarios=[],
            risk_notes=["note"],
        ),
        narrative=Narrative(summary="Short summary."),
    )
    out = insight_payload_to_dict(
        partial,
        symbol="ES",
        interval="5m",
        insight_id=UUID("00000000-0000-4000-8000-000000000001"),
        generated_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        retrieval=RetrievalBlock(chunk_ids=["a", "b"], kb_version="1.0.0"),
    )
    assert out["schema_version"] == "1.0.0"
    assert out["symbol"] == "ES"
    assert out["retrieval"]["chunk_ids"] == ["a", "b"]
