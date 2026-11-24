"""Persisted investigation HTTP results.

Revision ID: 0005_investigations
Revises: 0004_users_and_audit
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_investigations"
down_revision: str | None = "0004_users_and_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigations_status", "investigations", ["status"], unique=False)
    op.create_index("ix_investigations_updated", "investigations", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_investigations_updated", table_name="investigations")
    op.drop_index("ix_investigations_status", table_name="investigations")
    op.drop_table("investigations")
