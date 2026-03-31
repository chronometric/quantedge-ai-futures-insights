"""API health endpoint tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from quantedge_backend.main import app


@pytest.mark.asyncio
async def test_health_live() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "environment" in body


@pytest.mark.asyncio
async def test_health_ready() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/v1/health/ready")
    assert r.status_code == 200
