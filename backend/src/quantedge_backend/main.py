"""FastAPI entrypoint."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from starlette.responses import Response

from quantedge_backend import __version__
from quantedge_backend.api.v1.health import router as health_router
from quantedge_backend.api.v1.insights import router as insights_router
from quantedge_backend.api.v1.market import router as market_router
from quantedge_backend.api.ws import ConnectionManager
from quantedge_backend.api.ws import router as ws_router
from quantedge_backend.db.bars_repo import apply_retention
from quantedge_backend.db.migrate import is_sqlite_url, run_alembic_upgrade
from quantedge_backend.db.session import (
    create_all_tables,
    dispose_engine,
    init_engine,
    session_scope,
)
from quantedge_backend.market.stream import MarketRuntimeState, run_mock_pipeline
from quantedge_backend.observability.logging_config import configure_logging
from quantedge_backend.observability.metrics import prometheus_text
from quantedge_backend.observability.middleware import CorrelationIdMiddleware
from quantedge_backend.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_engine(settings.database_url)
    if is_sqlite_url(settings.database_url):
        await create_all_tables()
    else:
        await asyncio.to_thread(run_alembic_upgrade, settings.database_url)
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
    app.state.ws_manager = ConnectionManager()
    task: asyncio.Task[None] | None = None
    if settings.mock_market_data:
        task = asyncio.create_task(
            run_mock_pipeline(
                settings,
                redis,
                app.state.market_state,
                ws_manager=app.state.ws_manager,
            ),
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
    configure_logging(settings)
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
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(health_router)
    app.include_router(market_router)
    app.include_router(insights_router)
    app.include_router(ws_router)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(
            content=prometheus_text(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


app = create_app()
