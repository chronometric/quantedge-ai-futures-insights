"""Background orchestration: insights after pipeline events."""

from __future__ import annotations

import structlog

from quantedge_backend.api.ws import ConnectionManager
from quantedge_backend.db.session import session_scope
from quantedge_backend.llm.insight_service import generate_insight
from quantedge_backend.observability.metrics import inc
from quantedge_backend.settings import Settings

log = structlog.get_logger("orchestrator")


async def emit_insight_after_bar(
    symbol: str,
    settings: Settings,
    ws_manager: ConnectionManager,
) -> None:
    """Generate insight and push to WebSocket ``insights:{SYMBOL}``."""
    try:
        async with session_scope() as session:
            payload = await generate_insight(
                session,
                settings,
                symbol=symbol,
                interval="5m",
                lookback=120,
                include_narrative=True,
            )
        inc("quantedge_insights_generated_total")
        ch = f"insights:{symbol.upper()}"
        await ws_manager.broadcast(
            ch,
            {
                "type": "insight",
                "schema_version": "1.0.0",
                "data": payload,
            },
        )
    except Exception as e:  # noqa: BLE001 — background task; never crash pipeline
        log.warning("insight_emit_failed", symbol=symbol, error=str(e))
