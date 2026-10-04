"""SQLAlchemy models for the synthetic industrial plant."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
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
    """Maintenance work order. Protected creates require human approval."""

    __tablename__ = "work_orders"
    __table_args__ = (
        Index("ix_work_orders_number", "number", unique=True),
        Index("ix_work_orders_equipment_created", "equipment_id", "created_at"),
        Index("ix_work_orders_idempotency", "idempotency_key", unique=True),
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
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_investigation_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    equipment: Mapped[Equipment] = relationship(back_populates="work_orders")


class Document(Base):
    """Ingested technical document (fictional manuals in the demo)."""

    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_source_path", "source_path", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    source_path: Mapped[str] = mapped_column(String(512), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    equipment_codes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document")


class DocumentChunk(Base):
    """Embedded chunk used for retrieval."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_doc_index"),
        Index("ix_document_chunks_document", "document_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str] = mapped_column(String(512), nullable=False)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    embedding: Mapped[list[float]] = mapped_column(Vector(256), nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")


class ApprovalRequest(Base):
    """Human-approval queue row. Graph checkpoints remain the resume source of truth."""

    __tablename__ = "approval_requests"
    __table_args__ = (Index("ix_approval_requests_status", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    investigation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    thread_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    proposal: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
