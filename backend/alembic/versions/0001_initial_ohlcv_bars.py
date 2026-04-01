"""Initial ohlcv_bars table.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-01

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ohlcv_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("interval", sa.String(length=16), nullable=False),
        sa.Column("time_open", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_close", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Double(), nullable=False),
        sa.Column("high", sa.Double(), nullable=False),
        sa.Column("low", sa.Double(), nullable=False),
        sa.Column("close", sa.Double(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "interval",
            "time_open",
            name="uq_ohlcv_symbol_interval_open",
        ),
    )
    op.create_index(
        "ix_ohlcv_symbol_interval_time",
        "ohlcv_bars",
        ["symbol", "interval", "time_open"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ohlcv_symbol_interval_time", table_name="ohlcv_bars")
    op.drop_table("ohlcv_bars")
