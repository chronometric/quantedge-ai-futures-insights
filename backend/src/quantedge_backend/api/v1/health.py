"""Health and readiness endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from quantedge_backend import __version__
from quantedge_backend.api.deps import get_redis
from quantedge_backend.market.stream import verify_postgres, verify_redis
from quantedge_backend.settings import get_settings

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
def health_live() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.app_env,
    }


@router.get("/health/ready")
async def health_ready(redis: Annotated[Redis, Depends(get_redis)]) -> dict[str, Any]:
    settings = get_settings()
    errors: list[str] = []
    try:
        await verify_postgres()
    except Exception as e:  # noqa: BLE001 — surface dependency failures
        errors.append(f"postgres:{e!s}")
    try:
        await verify_redis(redis)
    except Exception as e:  # noqa: BLE001
        errors.append(f"redis:{e!s}")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "errors": errors},
        )
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.app_env,
    }
