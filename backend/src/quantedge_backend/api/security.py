"""Optional API key and rate limits for expensive endpoints."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from quantedge_backend.observability.metrics import inc
from quantedge_backend.settings import Settings, get_settings


def client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _extract_api_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    key = request.headers.get("X-API-Key")
    return key.strip() if key else None


async def require_api_key_if_configured(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """When ``API_KEY`` is set, require ``Authorization: Bearer`` or ``X-API-Key``."""
    expected = settings.api_key
    if not expected:
        return
    token = _extract_api_token(request)
    if token != expected:
        inc("quantedge_api_key_rejected_total")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


async def enforce_insight_rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Fixed-window per-minute limit per client IP (Redis). ``0`` disables."""
    limit = settings.insights_rate_limit_per_minute
    if limit <= 0:
        return
    redis = request.app.state.redis
    ip = client_ip(request)
    bucket = int(time.time() // 60)
    key = f"quantedge:rl:insight:{ip}:{bucket}"
    n = await redis.incr(key)
    if n == 1:
        await redis.expire(key, 120)
    if n > limit:
        inc("quantedge_rate_limit_exceeded_total")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Insight rate limit exceeded; try again later.",
            headers={"Retry-After": "60"},
        )
