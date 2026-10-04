"""Deterministic data access used by the HTTP API and MCP tool handlers."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.domain.models import Alarm, Equipment, MaintenanceRecord, SensorReading, WorkOrder
from forgeflow.domain.schemas import (
    AlarmOut,
    EquipmentOut,
    MaintenanceRecordOut,
    SensorReadingOut,
    WorkOrderOut,
)
from forgeflow.domain.seed.constants import DEFAULT_HISTORY_LIMIT, LOOKBACK_DAYS, MAX_HISTORY_LIMIT
from forgeflow.errors import ForgeFlowError, NotFoundError


class IndustrialQueryService:
    """Deterministic data access used by the HTTP API and MCP tool handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_equipment(self) -> list[EquipmentOut]:
        rows = (await self._session.scalars(select(Equipment).order_by(Equipment.code.asc()))).all()
        return [EquipmentOut.model_validate(row) for row in rows]

    async def get_equipment(self, code: str) -> EquipmentOut:
        row = await self._require_equipment(code)
        return EquipmentOut.model_validate(row)

    async def sensor_history(
        self,
        code: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[SensorReadingOut]:
        equipment = await self._require_equipment(code)
        window_start, window_end, bounded_limit = _normalize_window(start, end, limit)
        stmt = (
            select(SensorReading)
            .where(SensorReading.equipment_id == equipment.id)
            .where(SensorReading.recorded_at >= window_start)
            .where(SensorReading.recorded_at <= window_end)
            .order_by(SensorReading.recorded_at.asc())
            .limit(bounded_limit)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [_sensor_out(row) for row in rows]

    async def alarm_history(
        self,
        code: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> list[AlarmOut]:
        equipment = await self._require_equipment(code)
        window_start, window_end, bounded_limit = _normalize_window(start, end, limit)
        stmt = (
            select(Alarm)
            .where(Alarm.equipment_id == equipment.id)
            .where(Alarm.occurred_at >= window_start)
            .where(Alarm.occurred_at <= window_end)
            .order_by(Alarm.occurred_at.desc())
            .limit(bounded_limit)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [_alarm_out(row) for row in rows]

    async def maintenance_history(self, code: str) -> list[MaintenanceRecordOut]:
        equipment = await self._require_equipment(code)
        stmt = (
            select(MaintenanceRecord)
            .where(MaintenanceRecord.equipment_id == equipment.id)
            .order_by(MaintenanceRecord.performed_at.desc())
        )
        rows = (await self._session.scalars(stmt)).all()
        return [MaintenanceRecordOut.model_validate(row) for row in rows]

    async def work_orders(self, code: str) -> list[WorkOrderOut]:
        equipment = await self._require_equipment(code)
        stmt = (
            select(WorkOrder)
            .where(WorkOrder.equipment_id == equipment.id)
            .order_by(WorkOrder.created_at.desc())
        )
        rows = (await self._session.scalars(stmt)).all()
        return [WorkOrderOut.model_validate(row) for row in rows]

    async def create_work_order(
        self,
        *,
        equipment_id: str,
        title: str,
        description: str,
        priority: str,
        idempotency_key: str,
        source_investigation_id: str | None = None,
    ) -> WorkOrderOut:
        existing = await self._session.scalar(
            select(WorkOrder).where(WorkOrder.idempotency_key == idempotency_key)
        )
        if existing is not None:
            return WorkOrderOut.model_validate(existing)
        equipment = await self._require_equipment(equipment_id)
        now = datetime.now(UTC)
        investigation_uuid = parse_equipment_id(source_investigation_id or "")
        row = WorkOrder(
            id=uuid4(),
            equipment_id=equipment.id,
            number=f"WO-{uuid4().hex[:8].upper()}",
            title=title.strip(),
            description=description.strip(),
            status="open",
            priority=priority.strip() or "high",
            created_at=now,
            updated_at=now,
            completed_at=None,
            idempotency_key=idempotency_key,
            source_investigation_id=investigation_uuid,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            replay = await self._session.scalar(
                select(WorkOrder).where(WorkOrder.idempotency_key == idempotency_key)
            )
            if replay is None:
                raise
            return WorkOrderOut.model_validate(replay)
        await self._session.commit()
        return WorkOrderOut.model_validate(row)

    async def _require_equipment(self, code_or_id: str) -> Equipment:
        normalized = code_or_id.strip()
        if not normalized:
            raise NotFoundError("Equipment was not found")
        parsed_id = parse_equipment_id(normalized)
        if parsed_id is not None:
            stmt = select(Equipment).where(Equipment.id == parsed_id)
        else:
            stmt = select(Equipment).where(Equipment.code == normalized)
        row = await self._session.scalar(stmt)
        if row is None:
            raise NotFoundError(f"Equipment {normalized} was not found")
        return row


def _sensor_out(row: SensorReading) -> SensorReadingOut:
    return SensorReadingOut(
        id=row.id,
        equipment_id=row.equipment_id,
        timestamp=row.recorded_at,
        temperature=row.temperature,
        vibration=row.vibration,
        pressure=row.pressure,
        rpm=row.rpm,
        power_consumption=row.power_consumption,
        coolant_flow=row.coolant_flow,
        status=row.status,
    )


def _alarm_out(row: Alarm) -> AlarmOut:
    return AlarmOut(
        id=row.id,
        equipment_id=row.equipment_id,
        timestamp=row.occurred_at,
        code=row.code,
        severity=row.severity,
        message=row.message,
        acknowledged_at=row.acknowledged_at,
        cleared_at=row.cleared_at,
    )


def _normalize_window(
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> tuple[datetime, datetime, int]:
    if limit < 1 or limit > MAX_HISTORY_LIMIT:
        raise ForgeFlowError(
            f"limit must be between 1 and {MAX_HISTORY_LIMIT}",
            code="validation_error",
            status_code=422,
        )
    window_end = _as_utc(end) if end is not None else datetime.now(UTC)
    window_start = (
        _as_utc(start) if start is not None else window_end - timedelta(days=LOOKBACK_DAYS)
    )
    if window_end < window_start:
        raise ForgeFlowError(
            "end must be greater than or equal to start",
            code="validation_error",
            status_code=422,
        )
    return window_start, window_end, limit


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_equipment_id(value: str) -> UUID | None:
    """Return a UUID if `value` is one; otherwise treat it as an equipment code."""
    try:
        return UUID(value)
    except ValueError:
        return None
