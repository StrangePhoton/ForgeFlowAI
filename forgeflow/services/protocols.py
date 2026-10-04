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
    """Read-only plant queries. MCP tools wrap this; the agent must not query tables."""

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
