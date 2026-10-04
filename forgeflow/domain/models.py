"""SQLAlchemy models for the synthetic industrial plant."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forgeflow.db.base import Base


class Equipment(Base):
    """Asset registry entry. `code` is the operator-facing identifier (CNC-042)."""

    __tablename__ = "equipment"
    __table_args__ = (Index("ix_equipment_code", "code", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    sensor_readings: Mapped[list[SensorReading]] = relationship(back_populates="equipment")
    alarms: Mapped[list[Alarm]] = relationship(back_populates="equipment")
    maintenance_records: Mapped[list[MaintenanceRecord]] = relationship(back_populates="equipment")
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates="equipment")


class SensorReading(Base):
    """Point-in-time telemetry for one asset."""

    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint("equipment_id", "recorded_at", name="uq_sensor_readings_equipment_time"),
        Index("ix_sensor_readings_equipment_time", "equipment_id", "recorded_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    equipment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    vibration: Mapped[float] = mapped_column(Float, nullable=False)
    pressure: Mapped[float] = mapped_column(Float, nullable=False)
    rpm: Mapped[float] = mapped_column(Float, nullable=False)
    power_consumption: Mapped[float] = mapped_column(Float, nullable=False)
    coolant_flow: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    equipment: Mapped[Equipment] = relationship(back_populates="sensor_readings")


class Alarm(Base):
    """Equipment alarm event."""

    __tablename__ = "alarms"
    __table_args__ = (Index("ix_alarms_equipment_time", "equipment_id", "occurred_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    equipment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    equipment: Mapped[Equipment] = relationship(back_populates="alarms")


class MaintenanceRecord(Base):
    """Completed or deferred maintenance activity."""

    __tablename__ = "maintenance_records"
    __table_args__ = (Index("ix_maintenance_equipment_time", "equipment_id", "performed_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    equipment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    technician: Mapped[str] = mapped_column(String(128), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    equipment: Mapped[Equipment] = relationship(back_populates="maintenance_records")


class WorkOrder(Base):
    """Maintenance work order. Writes are not exposed in Milestone 1."""

    __tablename__ = "work_orders"
    __table_args__ = (
        Index("ix_work_orders_number", "number", unique=True),
        Index("ix_work_orders_equipment_created", "equipment_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    equipment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    equipment: Mapped[Equipment] = relationship(back_populates="work_orders")
