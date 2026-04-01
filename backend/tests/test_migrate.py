"""Phase 9 — Alembic URL helpers."""

from __future__ import annotations

from quantedge_backend.db.migrate import database_url_to_sync, is_sqlite_url


def test_is_sqlite_url() -> None:
    assert is_sqlite_url("sqlite+aiosqlite:///:memory:")
    assert not is_sqlite_url("postgresql+asyncpg://u:p@localhost:5432/quantedge")


def test_database_url_to_sync() -> None:
    assert (
        database_url_to_sync("postgresql+asyncpg://u:p@localhost:5432/quantedge")
        == "postgresql+psycopg://u:p@localhost:5432/quantedge"
    )
