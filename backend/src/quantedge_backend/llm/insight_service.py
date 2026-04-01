"""RAG + LLM (or mock) insight pipeline."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from quantedge_backend.db.bars_repo import list_bars
from quantedge_backend.features.snapshot import MIN_BARS, build_market_features
from quantedge_backend.llm.schemas import (
    EDUCATIONAL_DISCLAIMER,
    KeyLevel,
    LlmInsightPartial,
    Narrative,
    RetrievalBlock,
    Scenario,
    StructuredInsight,
    insight_payload_to_dict,
)
from quantedge_backend.rag.retrieve import RetrievedChunk, retrieve_for_snapshot
from quantedge_backend.settings import Settings

Bias = Literal["bullish", "bearish", "neutral"]

SYSTEM_PROMPT = """You are QuantEdge AI, a futures analytics assistant.
Rules:
- Ground reasoning ONLY in RETRIEVED_CONTEXT and MARKET_SNAPSHOT JSON.
  If context is insufficient, set bias to neutral, explain in risk_notes,
  and do not invent prices or events.
- Output a single JSON object with keys "structured" and "narrative" only.
  No markdown fences.
- "structured": bias, key_levels, scenarios (max 5), risk_notes.
- "narrative": "summary" (string). Optional trade_ideas (max 3), thesis required.
- Never promise returns or certainty."""


def _use_real_llm(settings: Settings) -> bool:
    if settings.testing:
        return False
    if settings.rag_mock_insights:
        return False
    return bool(settings.openai_api_key)


def _map_level_kind(k: str) -> str:
    if k in {"support", "resistance", "pivot", "target", "stop", "other"}:
        if k == "pivot":
            return "other"
        if k == "stop":
            return "invalidation"
        return k
    return "other"


def build_mock_insight(
    *,
    symbol: str,
    interval: str,
    market_features: dict[str, Any],
    chunk_ids: list[str],
    kb_version: str,
) -> dict[str, Any]:
    """Deterministic insight when LLM is disabled (tests / no API key)."""
    tr = str(market_features.get("trend_regime", "neutral"))
    bias: Bias = "neutral"
    if tr == "bullish":
        bias = "bullish"
    elif tr == "bearish":
        bias = "bearish"
    raw_levels = market_features.get("levels") or []
    key_levels: list[KeyLevel] = []
    for lv in raw_levels[:6]:
        if not isinstance(lv, dict) or "price" not in lv:
            continue
        role_str = _map_level_kind(str(lv.get("kind", "other")))
        prio = None
        st = lv.get("strength")
        if isinstance(st, (int, float)):
            prio = max(1, min(5, int(float(st) * 5)))
        key_levels.append(
            KeyLevel(
                price=float(lv["price"]),
                role=role_str,  # type: ignore[arg-type]
                priority=prio,
            ),
        )

    scenarios = [
        Scenario(
            name="Hold / wait",
            condition="Insufficient edge in snapshot; see risk_notes.",
            implication="Stand aside until structure clarifies.",
        ),
    ]
    risk_notes = [
        "Mock insight path (no LLM). Verify against live data.",
        f"Volatility regime: {market_features.get('volatility_regime', 'unknown')}.",
    ]
    structured = StructuredInsight(
        bias=bias,
        key_levels=key_levels,
        scenarios=scenarios,
        risk_notes=risk_notes,
    )
    narrative = Narrative(
        summary=(
            f"{symbol} {interval}: trend {tr}, vol "
            f"{market_features.get('volatility_regime', 'unknown')}. "
            "See structured levels; educational only."
        ),
    )
    partial = LlmInsightPartial(structured=structured, narrative=narrative)
    retrieval = RetrievalBlock(chunk_ids=chunk_ids, kb_version=kb_version)
    return insight_payload_to_dict(
        partial,
        symbol=symbol,
        interval=interval,
        insight_id=uuid4(),
        generated_at=datetime.now(UTC),
        retrieval=retrieval,
        disclaimer=EDUCATIONAL_DISCLAIMER,
    )


def _format_retrieved(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for i, ch in enumerate(chunks, 1):
        parts.append(f"--- Chunk {i} id={ch.chunk_id} ---\n{ch.document}")
    return "\n\n".join(parts) if parts else "(no chunks retrieved; ingest KB or widen filters.)"


async def generate_insight(
    session: AsyncSession,
    settings: Settings,
    *,
    symbol: str,
    interval: str,
    lookback: int,
    include_narrative: bool,
) -> dict[str, Any]:
    rows = await list_bars(
        session,
        symbol=symbol,
        interval=interval,
        start=None,
        end=None,
        limit=lookback,
    )
    if len(rows) < MIN_BARS:
        msg = f"need at least {MIN_BARS} bars for features, got {len(rows)}"
        raise ValueError(msg)

    market_features = build_market_features(
        rows,
        symbol=symbol,
        interval=interval,
        token_budget=None,
    )
    chunks = await retrieve_for_snapshot(settings, market_features)
    chunk_ids = [c.chunk_id for c in chunks]

    if not _use_real_llm(settings):
        return build_mock_insight(
            symbol=symbol,
            interval=interval,
            market_features=market_features,
            chunk_ids=chunk_ids,
            kb_version=settings.kb_version,
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    user_prompt = f"""MARKET_SNAPSHOT:
{json.dumps(market_features, default=str)}

RETRIEVED_CONTEXT:
{_format_retrieved(chunks)}

TASK: Produce JSON with "structured" and "narrative" as specified.
Include at most 3 trade ideas only if appropriate; else omit or use [].
Narrative: {"full detail" if include_narrative else "concise summary under 800 chars."}"""

    resp = await client.chat.completions.create(
        model=settings.rag_chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=2500,
    )
    raw = resp.choices[0].message.content
    if not raw:
        msg = "empty LLM response"
        raise RuntimeError(msg)
    partial = LlmInsightPartial.model_validate_json(raw)
    if not include_narrative:
        partial = LlmInsightPartial(
            structured=partial.structured,
            narrative=Narrative(summary=partial.narrative.summary[:800]),
        )
    retrieval = RetrievalBlock(chunk_ids=chunk_ids, kb_version=settings.kb_version)
    return insight_payload_to_dict(
        partial,
        symbol=symbol,
        interval=interval,
        insight_id=uuid4(),
        generated_at=datetime.now(UTC),
        retrieval=retrieval,
        disclaimer=EDUCATIONAL_DISCLAIMER,
    )
