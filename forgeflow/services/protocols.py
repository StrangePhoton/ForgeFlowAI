"""Protocols for industrial read access."""

from datetime import datetime
from typing import Protocol

from forgeflow.domain.schemas import (
    AlarmOut,
    EquipmentOut,
    MaintenanceRecordOut,
    SensorReadingOut,
    WorkOrderOut,
)
from forgeflow.domain.seed.constants import DEFAULT_HISTORY_LIMIT


class IndustrialReader(Protocol):
    """Plant queries used by MCP tools. The agent must not query tables directly."""

    async def list_equipment(self) -> list[EquipmentOut]: ...

    async def get_equipment(self, code: str) -> EquipmentOut: ...

    async def sensor_history(
        self,
        code: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[SensorReadingOut]: ...

    async def alarm_history(
        self,
        code: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[AlarmOut]: ...

    async def maintenance_history(self, code: str) -> list[MaintenanceRecordOut]: ...

    async def work_orders(self, code: str) -> list[WorkOrderOut]: ...

    async def create_work_order(
        self,
        *,
        equipment_id: str,
        title: str,
        description: str,
        priority: str,
        idempotency_key: str,
        source_investigation_id: str | None = None,
    ) -> WorkOrderOut: ...
