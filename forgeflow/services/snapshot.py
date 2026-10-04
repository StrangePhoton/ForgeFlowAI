"""In-memory industrial reader used by unit tests and local MCP invocations."""

from datetime import datetime, timedelta

from forgeflow.domain.schemas import (
    AlarmOut,
    EquipmentOut,
    MaintenanceRecordOut,
    SensorReadingOut,
    WorkOrderOut,
)
from forgeflow.domain.seed.constants import DEFAULT_HISTORY_LIMIT, DEMO_CLOCK
from forgeflow.domain.seed.generate import EquipmentDraft, PlantSnapshot
from forgeflow.errors import NotFoundError


class InMemoryIndustrialReader:
    """Stand-in for IndustrialQueryService that never touches PostgreSQL."""

    def __init__(self, snapshot: PlantSnapshot) -> None:
        self._snapshot = snapshot

    async def list_equipment(self) -> list[EquipmentOut]:
        return [_equipment_out(item) for item in self._snapshot.equipment]

    async def get_equipment(self, code: str) -> EquipmentOut:
        return _equipment_out(self._require(code))

    async def sensor_history(
        self,
        code: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[SensorReadingOut]:
        self._require(code)
        window_start = start or DEMO_CLOCK - timedelta(days=30)
        window_end = end or DEMO_CLOCK
        rows = [
            row
            for row in self._snapshot.readings_for(code)
            if window_start <= row.timestamp <= window_end
        ][:limit]
        return [
            SensorReadingOut(
                id=row.id,
                equipment_id=row.equipment_id,
                timestamp=row.timestamp,
                temperature=row.temperature,
                vibration=row.vibration,
                pressure=row.pressure,
                rpm=row.rpm,
                power_consumption=row.power_consumption,
                coolant_flow=row.coolant_flow,
                status=row.status,
            )
            for row in rows
        ]

    async def alarm_history(
        self,
        code: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[AlarmOut]:
        self._require(code)
        window_start = start or DEMO_CLOCK - timedelta(days=30)
        window_end = end or DEMO_CLOCK
        rows = [
            row
            for row in self._snapshot.alarms_for(code)
            if window_start <= row.timestamp <= window_end
        ][:limit]
        return [
            AlarmOut(
                id=row.id,
                equipment_id=row.equipment_id,
                timestamp=row.timestamp,
                code=row.code,
                severity=row.severity,
                message=row.message,
                acknowledged_at=row.acknowledged_at,
                cleared_at=row.cleared_at,
            )
            for row in rows
        ]

    async def maintenance_history(self, code: str) -> list[MaintenanceRecordOut]:
        self._require(code)
        return [
            MaintenanceRecordOut(
                id=row.id,
                equipment_id=row.equipment_id,
                performed_at=row.performed_at,
                maintenance_type=row.maintenance_type,
                title=row.title,
                description=row.description,
                technician=row.technician,
                result=row.result,
                next_due_at=row.next_due_at,
            )
            for row in self._snapshot.maintenance_for(code)
        ]

    async def work_orders(self, code: str) -> list[WorkOrderOut]:
        self._require(code)
        return [
            WorkOrderOut(
                id=row.id,
                equipment_id=row.equipment_id,
                number=row.number,
                title=row.title,
                description=row.description,
                status=row.status,
                priority=row.priority,
                created_at=row.created_at,
                updated_at=row.updated_at,
                completed_at=row.completed_at,
            )
            for row in self._snapshot.work_orders_for(code)
        ]

    def _require(self, code: str) -> EquipmentDraft:
        normalized = code.strip()
        if not normalized:
            raise NotFoundError("Equipment was not found")
        try:
            return self._snapshot.equipment_by_code(normalized)
        except KeyError as exc:
            raise NotFoundError(f"Equipment {normalized} was not found") from exc


def _equipment_out(item: EquipmentDraft) -> EquipmentOut:
    return EquipmentOut(
        id=item.id,
        code=item.code,
        name=item.name,
        equipment_type=item.equipment_type,
        model=item.model,
        manufacturer=item.manufacturer,
        location=item.location,
        status=item.status,
        installed_at=item.installed_at,
        attributes=item.attributes,
    )
