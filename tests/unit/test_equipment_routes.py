"""HTTP equipment routes with an in-memory fake service."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.schemas import (
    AlarmOut,
    EquipmentOut,
    MaintenanceRecordOut,
    SensorReadingOut,
    WorkOrderOut,
)
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import EquipmentDraft, PlantSnapshot, generate_plant
from forgeflow.errors import NotFoundError

SEED_NOW = DEMO_CLOCK


class SnapshotQueryService:
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
        limit: int = 2000,
    ) -> list[SensorReadingOut]:
        self._require(code)
        window_start = start or SEED_NOW - timedelta(days=30)
        window_end = end or SEED_NOW
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
        limit: int = 2000,
    ) -> list[AlarmOut]:
        self._require(code)
        window_start = start or SEED_NOW - timedelta(days=30)
        window_end = end or SEED_NOW
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
        try:
            return self._snapshot.equipment_by_code(code)
        except KeyError as exc:
            raise NotFoundError(f"Equipment {code} was not found") from exc


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


def _install_fake(client: TestClient) -> PlantSnapshot:
    snapshot = generate_plant(now=SEED_NOW)
    fake = SnapshotQueryService(snapshot)
    client.app.dependency_overrides[get_industrial_service] = lambda: fake
    return snapshot


def test_list_and_get_cnc_042(client: TestClient) -> None:
    _install_fake(client)
    listed = client.get("/api/v1/equipment")
    assert listed.status_code == 200
    codes = {item["code"] for item in listed.json()}
    assert "CNC-042" in codes
    detail = client.get("/api/v1/equipment/CNC-042")
    assert detail.status_code == 200
    body = detail.json()
    assert body["code"] == "CNC-042"
    assert body["model"] == "FX-400"


def test_unknown_equipment_returns_not_found(client: TestClient) -> None:
    _install_fake(client)
    response = client.get("/api/v1/equipment/UNKNOWN-1")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_cnc_history_endpoints(client: TestClient) -> None:
    _install_fake(client)
    start = (SEED_NOW - timedelta(days=30)).isoformat()
    end = SEED_NOW.isoformat()
    telemetry = client.get(
        "/api/v1/equipment/CNC-042/sensor-history",
        params={"start": start, "end": end},
    )
    alarms = client.get(
        "/api/v1/equipment/CNC-042/alarm-history",
        params={"start": start, "end": end},
    )
    maintenance = client.get("/api/v1/equipment/CNC-042/maintenance-history")
    work_orders = client.get("/api/v1/equipment/CNC-042/work-orders")
    assert telemetry.status_code == 200
    assert alarms.status_code == 200
    assert maintenance.status_code == 200
    assert work_orders.status_code == 200
    assert len(telemetry.json()) > 100
    assert any(item["code"] == "TEMP_HIGH" for item in alarms.json())
    assert any(item["title"] == "Cooling system inspection" for item in maintenance.json())
    assert work_orders.json() == []
