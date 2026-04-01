"""Retrieve KB chunks for a market snapshot query."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, cast

from quantedge_backend.rag.chroma_store import get_kb_collection
from quantedge_backend.settings import Settings


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    document: str
    distance: float | None
    metadata: dict[str, Any]


def _where_filter(volatility_regime: str | None) -> dict[str, Any] | None:
    """Match universal chunks (regime=any) or regime-specific rows."""
    if not volatility_regime or volatility_regime == "unknown":
        return {"regime": "any"}
    return {
        "$or": [
            {"regime": "any"},
            {"regime": volatility_regime},
        ]
    }


async def retrieve_for_snapshot(
    settings: Settings,
    market_features: dict[str, Any],
    *,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Embedding similarity over JSON snapshot + optional volatility regime filter."""
    k = top_k if top_k is not None else settings.rag_top_k
    query_text = json.dumps(market_features, separators=(",", ":"), default=str)[:12000]
    vol = market_features.get("volatility_regime")
    where = _where_filter(str(vol) if vol is not None else None)

    def _query() -> dict[str, Any]:
        col = get_kb_collection(settings)
        try:
            return cast(
                dict[str, Any],
                col.query(
                    query_texts=[query_text],
                    n_results=k,
                    where=where,
                    include=["documents", "distances", "metadatas"],
                ),
            )
        except Exception:
            return cast(
                dict[str, Any],
                col.query(
                    query_texts=[query_text],
                    n_results=k,
                    include=["documents", "distances", "metadatas"],
                ),
            )

    raw = await asyncio.to_thread(_query)
    out: list[RetrievedChunk] = []
    ids_list = raw.get("ids") or []
    docs_list = raw.get("documents") or []
    dist_list = raw.get("distances") or []
    meta_list = raw.get("metadatas") or []
    if not ids_list or not ids_list[0]:
        return out
    ids = ids_list[0]
    docs = docs_list[0]
    dists = dist_list[0] if dist_list else [None] * len(ids)
    metas = meta_list[0] if meta_list else [{}] * len(ids)
    for i, cid in enumerate(ids):
        di = dists[i] if i < len(dists) else None
        dist: float | None
        if di is None:
            dist = None
        elif isinstance(di, (int, float)):
            dist = float(di)
        else:
            dist = float(cast(Any, di))
        doc = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        out.append(
            RetrievedChunk(
                chunk_id=str(cid),
                document=str(doc),
                distance=dist,
                metadata=dict(meta) if isinstance(meta, dict) else {},
            ),
        )
    return out
