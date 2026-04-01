"""API health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from quantedge_backend.main import app


def test_health_live() -> None:
    with TestClient(app) as client:
        r = client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "environment" in body


def test_health_ready() -> None:
    with TestClient(app) as client:
        r = client.get("/v1/health/ready")
    assert r.status_code == 200


def test_symbols_list() -> None:
    with TestClient(app) as client:
        r = client.get("/v1/symbols")
    assert r.status_code == 200
    body = r.json()
    assert "symbols" in body
    assert isinstance(body["symbols"], list)
