"""Equipment registry and operational history endpoints."""

from datetime import datetime

from fastapi import APIRouter, Query

from forgeflow.api.deps import IndustrialServiceDep
from forgeflow.domain.schemas import (
    AlarmOut,
    EquipmentOut,
    MaintenanceRecordOut,
    SensorReadingOut,
    WorkOrderOut,
)
from forgeflow.domain.seed.constants import DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(service: IndustrialServiceDep) -> list[EquipmentOut]:
    return await service.list_equipment()


@router.get("/{code}", response_model=EquipmentOut)
async def get_equipment(code: str, service: IndustrialServiceDep) -> EquipmentOut:
    return await service.get_equipment(code)


@router.get("/{code}/sensor-history", response_model=list[SensorReadingOut])
async def get_sensor_history(
    code: str,
    service: IndustrialServiceDep,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT),
) -> list[SensorReadingOut]:
    return await service.sensor_history(code, start=start, end=end, limit=limit)


@router.get("/{code}/alarm-history", response_model=list[AlarmOut])
async def get_alarm_history(
    code: str,
    service: IndustrialServiceDep,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT),
) -> list[AlarmOut]:
    return await service.alarm_history(code, start=start, end=end, limit=limit)


@router.get("/{code}/maintenance-history", response_model=list[MaintenanceRecordOut])
async def get_maintenance_history(
    code: str, service: IndustrialServiceDep
) -> list[MaintenanceRecordOut]:
    return await service.maintenance_history(code)


@router.get("/{code}/work-orders", response_model=list[WorkOrderOut])
async def get_work_orders(code: str, service: IndustrialServiceDep) -> list[WorkOrderOut]:
    return await service.work_orders(code)
