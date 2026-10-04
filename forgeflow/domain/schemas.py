"""Pydantic schemas for industrial read APIs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    equipment_type: str
    model: str
    manufacturer: str
    location: str
    status: str
    installed_at: datetime
    attributes: dict[str, Any] = Field(default_factory=dict)


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_id: UUID
    timestamp: datetime
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    power_consumption: float
    coolant_flow: float | None
    status: str


class AlarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_id: UUID
    timestamp: datetime
    code: str
    severity: str
    message: str
    acknowledged_at: datetime | None
    cleared_at: datetime | None


class MaintenanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_id: UUID
    performed_at: datetime
    maintenance_type: str
    title: str
    description: str
    technician: str
    result: str
    next_due_at: datetime | None


class WorkOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_id: UUID
    number: str
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    idempotency_key: str | None = None
    source_investigation_id: UUID | None = None
