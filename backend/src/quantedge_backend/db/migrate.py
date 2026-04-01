"""Run Alembic migrations for PostgreSQL; SQLite uses create_all in session."""

from __future__ import annotations

from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config


def database_url_to_sync(database_url: str) -> str:
    """Use psycopg (sync) for the migration runner."""
    if "+asyncpg" in database_url:
        return database_url.replace("+asyncpg", "+psycopg", 1)
    return database_url


def _backend_root() -> Path:
    # quantedge_backend/db/migrate.py -> backend/
    return Path(__file__).resolve().parent.parent.parent.parent


def is_sqlite_url(database_url: str) -> bool:
    return "sqlite" in database_url.lower()


def run_alembic_upgrade(database_url: str) -> None:
    """Apply all Alembic revisions to head (PostgreSQL)."""
    sync_url = database_url_to_sync(database_url)
    root = _backend_root()
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", sync_url)
    upgrade(cfg, "head")
