"""Phase 10 — baseline security headers on HTTP responses."""

from __future__ import annotations

from fastapi.testclient import TestClient

from quantedge_backend.main import app


def test_security_headers_on_health() -> None:
    with TestClient(app) as client:
        r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
