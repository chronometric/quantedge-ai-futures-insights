"""Pydantic models aligned with ``contracts/insight-payload.schema.json``."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class KeyLevel(BaseModel):
    price: float
    role: Literal["support", "resistance", "target", "invalidation", "other"]
    priority: int | None = Field(default=None, ge=1, le=5)


class Scenario(BaseModel):
    name: str
    condition: str
    implication: str | None = None


class StructuredInsight(BaseModel):
    bias: Literal["bullish", "bearish", "neutral"]
    key_levels: list[KeyLevel] = Field(default_factory=list)
    scenarios: list[Scenario] = Field(default_factory=list, max_length=5)
    risk_notes: list[str] = Field(default_factory=list)


class TradeIdea(BaseModel):
    thesis: str
    horizon: Literal["intraday", "short_swing", "other"] | None = None
    invalidation: str | None = None


class Narrative(BaseModel):
    summary: str = Field(max_length=4000)
    trade_ideas: list[TradeIdea] = Field(default_factory=list, max_length=3)


class RetrievalBlock(BaseModel):
    chunk_ids: list[str] = Field(default_factory=list)
    kb_version: str | None = None


class LlmInsightPartial(BaseModel):
    """JSON object returned by the model (no ids / timestamps)."""

    structured: StructuredInsight
    narrative: Narrative


EDUCATIONAL_DISCLAIMER = (
    "Educational and analytical content only; not investment advice. "
    "Futures involve substantial risk of loss."
)


def insight_payload_to_dict(
    partial: LlmInsightPartial,
    *,
    symbol: str,
    interval: str | None,
    insight_id: UUID | None = None,
    generated_at: datetime | None = None,
    retrieval: RetrievalBlock | None = None,
    disclaimer: str | None = EDUCATIONAL_DISCLAIMER,
) -> dict[str, Any]:
    """Serialize a validated insight to API JSON (RFC 3339 with Z)."""
    iid = insight_id or uuid4()
    ts = generated_at or datetime.now(UTC)
    gen = ts.isoformat().replace("+00:00", "Z")
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "insight_id": str(iid),
        "symbol": symbol.upper(),
        "generated_at": gen,
        "structured": partial.structured.model_dump(mode="json"),
        "narrative": partial.narrative.model_dump(mode="json"),
    }
    if interval:
        payload["interval"] = interval
    if retrieval is not None:
        payload["retrieval"] = retrieval.model_dump(mode="json")
    if disclaimer:
        payload["disclaimer"] = disclaimer
    return payload
