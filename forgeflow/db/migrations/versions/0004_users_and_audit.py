"""Operator accounts and security audit events.

Revision ID: 0004_users_and_audit
Revises: 0003_retrieval_and_approvals
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_users_and_audit"
down_revision: str | None = "0003_retrieval_and_approvals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("tool_name", sa.String(length=64), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("investigation_id", sa.String(length=64), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_occurred", "audit_events", ["occurred_at"], unique=False)
    op.create_index("ix_audit_events_type", "audit_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_type", table_name="audit_events")
    op.drop_index("ix_audit_events_occurred", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
