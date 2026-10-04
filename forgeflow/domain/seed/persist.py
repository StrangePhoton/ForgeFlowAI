"""Persist a generated plant snapshot into PostgreSQL."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.domain.models import Alarm, Equipment, MaintenanceRecord, SensorReading, WorkOrder
from forgeflow.domain.seed.generate import PlantSnapshot
from forgeflow.observability.logging import get_logger

logger = get_logger(__name__)


async def persist_plant(session: AsyncSession, snapshot: PlantSnapshot, *, reset: bool) -> None:
    """Insert synthetic rows. `reset=True` replaces any existing industrial data."""
    if reset:
        await session.execute(delete(WorkOrder))
        await session.execute(delete(MaintenanceRecord))
        await session.execute(delete(Alarm))
        await session.execute(delete(SensorReading))
        await session.execute(delete(Equipment))
    else:
        existing = await session.scalar(select(func.count()).select_from(Equipment))
        if existing:
            logger.info(
                "seed_skipped", extra={"forgeflow": {"reason": "equipment_already_present"}}
            )
            return

    session.add_all(
        [
            Equipment(
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
            for item in snapshot.equipment
        ]
    )
    session.add_all(
        [
            SensorReading(
                id=item.id,
                equipment_id=item.equipment_id,
                recorded_at=item.timestamp,
                temperature=item.temperature,
                vibration=item.vibration,
                pressure=item.pressure,
                rpm=item.rpm,
                power_consumption=item.power_consumption,
                coolant_flow=item.coolant_flow,
                status=item.status,
            )
            for item in snapshot.readings
        ]
    )
    session.add_all(
        [
            Alarm(
                id=item.id,
                equipment_id=item.equipment_id,
                occurred_at=item.timestamp,
                code=item.code,
                severity=item.severity,
                message=item.message,
                acknowledged_at=item.acknowledged_at,
                cleared_at=item.cleared_at,
            )
            for item in snapshot.alarms
        ]
    )
    session.add_all(
        [
            MaintenanceRecord(
                id=item.id,
                equipment_id=item.equipment_id,
                performed_at=item.performed_at,
                maintenance_type=item.maintenance_type,
                title=item.title,
                description=item.description,
                technician=item.technician,
                result=item.result,
                next_due_at=item.next_due_at,
            )
            for item in snapshot.maintenance
        ]
    )
    session.add_all(
        [
            WorkOrder(
                id=item.id,
                equipment_id=item.equipment_id,
                number=item.number,
                title=item.title,
                description=item.description,
                status=item.status,
                priority=item.priority,
                created_at=item.created_at,
                updated_at=item.updated_at,
                completed_at=item.completed_at,
            )
            for item in snapshot.work_orders
        ]
    )
    logger.info(
        "seed_persisted",
        extra={
            "forgeflow": {
                "equipment": len(snapshot.equipment),
                "readings": len(snapshot.readings),
                "alarms": len(snapshot.alarms),
            }
        },
    )
