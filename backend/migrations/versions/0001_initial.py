"""initial baseline

Empty baseline revision. Adds no tables (no domain tables in Milestone 2);
gives Alembic a head so `upgrade head` succeeds and later milestones autogenerate
from a known base.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-29

"""
from collections.abc import Sequence

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
