"""Create industrial domain tables.

Revision ID: 0002_industrial_domain
Revises: 0001_enable_pgvector
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_industrial_domain"
down_revision: str | None = "0001_enable_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("equipment_type", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("manufacturer", sa.String(length=64), nullable=False),
        sa.Column("location", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_code", "equipment", ["code"], unique=True)

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("vibration", sa.Float(), nullable=False),
        sa.Column("pressure", sa.Float(), nullable=False),
        sa.Column("rpm", sa.Float(), nullable=False),
        sa.Column("power_consumption", sa.Float(), nullable=False),
        sa.Column("coolant_flow", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_id", "recorded_at", name="uq_sensor_readings_equipment_time"
        ),
    )
    op.create_index(
        "ix_sensor_readings_equipment_time",
        "sensor_readings",
        ["equipment_id", "recorded_at"],
        unique=False,
    )

    op.create_table(
        "alarms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_alarms_equipment_time",
        "alarms",
        ["equipment_id", "occurred_at"],
        unique=False,
    )

    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("maintenance_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("technician", sa.String(length=128), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_equipment_time",
        "maintenance_records",
        ["equipment_id", "performed_at"],
        unique=False,
    )

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_orders_number", "work_orders", ["number"], unique=True)
    op.create_index(
        "ix_work_orders_equipment_created",
        "work_orders",
        ["equipment_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_work_orders_equipment_created", table_name="work_orders")
    op.drop_index("ix_work_orders_number", table_name="work_orders")
    op.drop_table("work_orders")
    op.drop_index("ix_maintenance_equipment_time", table_name="maintenance_records")
    op.drop_table("maintenance_records")
    op.drop_index("ix_alarms_equipment_time", table_name="alarms")
    op.drop_table("alarms")
    op.drop_index("ix_sensor_readings_equipment_time", table_name="sensor_readings")
    op.drop_table("sensor_readings")
    op.drop_index("ix_equipment_code", table_name="equipment")
    op.drop_table("equipment")
