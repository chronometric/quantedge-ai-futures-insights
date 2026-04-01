"""Background task: mock 1m feed → 5m aggregation → Postgres + Redis."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from redis.asyncio import Redis
from sqlalchemy import text

from quantedge_backend.db.bars_repo import bar_to_contract_dict, upsert_five_minute_bar
from quantedge_backend.db.session import session_scope
from quantedge_backend.market.aggregate import FiveMinuteAggregator, align_one_minute_bar_open
from quantedge_backend.market.mock_provider import mock_one_minute_stream
from quantedge_backend.market.redis_cache import push_recent_bar, set_last_bar
from quantedge_backend.observability.metrics import inc
from quantedge_backend.settings import Settings

if TYPE_CHECKING:
    from quantedge_backend.api.ws import ConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class MarketRuntimeState:
    """Shared pipeline state for observability endpoints."""

    last_bar_close_utc: dict[str, str] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def record_5m_close(self, symbol: str, time_close_iso: str) -> None:
        sym = symbol.upper()
        async with self.lock:
            self.last_bar_close_utc[sym] = time_close_iso


async def run_mock_pipeline(
    settings: Settings,
    redis: Redis,
    state: MarketRuntimeState,
    *,
    ws_manager: ConnectionManager | None = None,
) -> None:
    symbols = settings.symbol_list()
    aggregators = {s: FiveMinuteAggregator() for s in symbols}
    stream = mock_one_minute_stream(symbols, tick_seconds=settings.mock_tick_seconds)
    async for sym, raw in stream:
        bar = align_one_minute_bar_open(raw)
        agg = aggregators[sym]
        completed, warnings = agg.add(bar)
        for w in warnings:
            logger.debug("%s: %s", sym, w)
        if completed is None:
            continue
        async with session_scope() as session:
            row = await upsert_five_minute_bar(
                session,
                symbol=sym,
                interval="5m",
                bar=completed,
                source="mock",
            )
        payload = bar_to_contract_dict(row)
        await set_last_bar(redis, sym, "5m", payload)
        await push_recent_bar(redis, sym, "5m", payload)
        close_iso = completed.time_close.isoformat().replace("+00:00", "Z")
        await state.record_5m_close(sym, close_iso)

        if ws_manager is not None and settings.ws_broadcast_enabled and not settings.testing:
            ch = f"market:{sym.upper()}:5m"
            inc("quantedge_pipeline_bars_emitted_total")
            await ws_manager.broadcast(
                ch,
                {"type": "bar", "schema_version": "1.0.0", "data": payload},
            )
            if settings.stream_insights_on_bar:
                from quantedge_backend.market.orchestrator import emit_insight_after_bar

                asyncio.create_task(emit_insight_after_bar(sym, settings, ws_manager))


async def verify_postgres() -> None:
    from quantedge_backend.db.session import get_engine

    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def verify_redis(redis: Redis) -> None:
    await redis.ping()
