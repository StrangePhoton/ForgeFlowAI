"""Pydantic schemas for MCP tool inputs and outputs."""

from datetime import datetime

from pydantic import BaseModel, Field

from forgeflow.domain.schemas import AlarmOut, MaintenanceRecordOut, SensorReadingOut
from forgeflow.domain.seed.constants import DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT

GET_EQUIPMENT = "get_equipment"
GET_SENSOR_HISTORY = "get_sensor_history"
GET_ALARM_HISTORY = "get_alarm_history"
GET_MAINTENANCE_HISTORY = "get_maintenance_history"

EQUIPMENT_TOOLS = (GET_EQUIPMENT, GET_SENSOR_HISTORY, GET_ALARM_HISTORY)
MAINTENANCE_TOOLS = (GET_MAINTENANCE_HISTORY,)
ALL_TOOLS = EQUIPMENT_TOOLS + MAINTENANCE_TOOLS


class EquipmentIdInput(BaseModel):
    equipment_id: str = Field(min_length=1, max_length=64)


class HistoryWindowInput(BaseModel):
    equipment_id: str = Field(min_length=1, max_length=64)
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT)


class SensorHistoryResult(BaseModel):
    count: int
    items: list[SensorReadingOut]


class AlarmHistoryResult(BaseModel):
    count: int
    items: list[AlarmOut]


class MaintenanceHistoryResult(BaseModel):
    count: int
    items: list[MaintenanceRecordOut]


class ToolInfo(BaseModel):
    name: str
    description: str
    server: str
    input_schema: dict[str, object]
