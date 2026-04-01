"""FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from quantedge_backend.db.session import get_session_factory
from quantedge_backend.market.stream import MarketRuntimeState


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
        await session.commit()


def get_redis(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis)


def get_market_state(request: Request) -> MarketRuntimeState:
    return cast(MarketRuntimeState, request.app.state.market_state)
