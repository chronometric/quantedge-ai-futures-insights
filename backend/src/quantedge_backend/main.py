"""FastAPI entrypoint (Phase 2 skeleton)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantedge_backend import __version__

_ENV = os.getenv("APP_ENV", "dev")


def create_app() -> FastAPI:
    app = FastAPI(
        title="QuantEdge AI API",
        version=__version__,
        description="Real-time futures insights engine (V1 skeleton).",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/v1/health")
    def health_live() -> dict[str, Any]:
        return {"status": "ok", "version": __version__, "environment": _ENV}

    @app.get("/v1/health/ready")
    def health_ready() -> dict[str, Any]:
        # Phase 3+: verify DB, Redis, vector store
        return {"status": "ok", "version": __version__, "environment": _ENV}

    return app


app = create_app()
