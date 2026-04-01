"""Correlation ID and request timing (structured logs)."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from quantedge_backend.observability.metrics import inc

log = structlog.get_logger("http")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Bind ``request_id`` (header ``X-Request-ID`` or new UUID) for structlog context."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=rid)
        request.state.request_id = rid
        t0 = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        response.headers["X-Request-ID"] = rid
        log.info(
            "request_complete",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(ms, 2),
        )
        inc("quantedge_http_requests_total")
        structlog.contextvars.clear_contextvars()
        return response
