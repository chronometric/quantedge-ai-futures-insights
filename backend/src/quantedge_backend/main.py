"""FastAPI entrypoint."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from quantedge_backend import __version__
from quantedge_backend.api.v1.health import router as health_router
from quantedge_backend.api.v1.market import router as market_router
from quantedge_backend.db.bars_repo import apply_retention
from quantedge_backend.db.session import (
    create_all_tables,
    dispose_engine,
    init_engine,
    session_scope,
)
from quantedge_backend.market.stream import MarketRuntimeState, run_mock_pipeline
from quantedge_backend.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_engine(settings.database_url)
    await create_all_tables()
    async with session_scope() as session:
        await apply_retention(session, retention_months=settings.retention_months)
    if settings.testing:
        import fakeredis.aioredis as fakeredis_aioredis

        redis = fakeredis_aioredis.FakeRedis(decode_responses=True)
    else:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    app.state.market_state = MarketRuntimeState()
    task: asyncio.Task[None] | None = None
    if settings.mock_market_data:
        task = asyncio.create_task(
            run_mock_pipeline(settings, redis, app.state.market_state),
        )
    yield
    if task is not None:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    aclose = getattr(redis, "aclose", None)
    if callable(aclose):
        await aclose()
    else:
        close = getattr(redis, "close", None)
        if callable(close):
            res = close()
            if asyncio.iscoroutine(res):
                await res
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app = FastAPI(
        title="QuantEdge AI API",
        version=__version__,
        description="Real-time futures insights engine (V1).",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(market_router)
    return app


app = create_app()
