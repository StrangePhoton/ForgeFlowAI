"""Deterministic in-memory plant generation. Persistence is a separate step."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any
from uuid import UUID, uuid5

from forgeflow.domain.enums import AlarmSeverity, SensorStatus
from forgeflow.domain.seed.catalog import (
    load_equipment_catalog,
    load_maintenance_catalog,
    load_work_order_catalog,
)
from forgeflow.domain.seed.constants import (
    CNC_ALARM_DAYS,
    CNC_CODE,
    CNC_HIGH_TEMP_SPIKE_DAYS,
    HISTORY_DAYS,
    LOOKBACK_DAYS,
    RNG_SEED,
    SEED_NAMESPACE,
    TEMP_HIGH_CODE,
    TEMP_HIGH_THRESHOLD_C,
)


@dataclass(frozen=True)
class EquipmentDraft:
    id: UUID
    code: str
    name: str
    equipment_type: str
    model: str
    manufacturer: str
    location: str
    status: str
    installed_at: datetime
    attributes: dict[str, Any]


@dataclass(frozen=True)
class ReadingDraft:
    id: UUID
    equipment_id: UUID
    equipment_code: str
    timestamp: datetime
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    power_consumption: float
    coolant_flow: float | None
    status: str


@dataclass(frozen=True)
class AlarmDraft:
    id: UUID
    equipment_id: UUID
    equipment_code: str
    timestamp: datetime
    code: str
    severity: str
    message: str
    acknowledged_at: datetime | None
    cleared_at: datetime | None


@dataclass(frozen=True)
class MaintenanceDraft:
    id: UUID
    equipment_id: UUID
    equipment_code: str
    performed_at: datetime
    maintenance_type: str
    title: str
    description: str
    technician: str
    result: str
    next_due_at: datetime | None


@dataclass(frozen=True)
class WorkOrderDraft:
    id: UUID
    equipment_id: UUID
    equipment_code: str
    number: str
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True)
class PlantSnapshot:
    generated_at: datetime
    equipment: tuple[EquipmentDraft, ...]
    readings: tuple[ReadingDraft, ...]
    alarms: tuple[AlarmDraft, ...]
    maintenance: tuple[MaintenanceDraft, ...]
    work_orders: tuple[WorkOrderDraft, ...]

    def equipment_by_code(self, code: str) -> EquipmentDraft:
        for item in self.equipment:
            if item.code == code:
                return item
        msg = f"Equipment {code} is not in the generated snapshot"
        raise KeyError(msg)

    def readings_for(self, code: str) -> tuple[ReadingDraft, ...]:
        return tuple(item for item in self.readings if item.equipment_code == code)

    def alarms_for(self, code: str) -> tuple[AlarmDraft, ...]:
        return tuple(item for item in self.alarms if item.equipment_code == code)

    def maintenance_for(self, code: str) -> tuple[MaintenanceDraft, ...]:
        return tuple(item for item in self.maintenance if item.equipment_code == code)

    def work_orders_for(self, code: str) -> tuple[WorkOrderDraft, ...]:
        return tuple(item for item in self.work_orders if item.equipment_code == code)


def stable_uuid(*parts: str) -> UUID:
    return uuid5(SEED_NAMESPACE, "|".join(parts))


@dataclass(frozen=True)
class ReadingValues:
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    power_consumption: float
    coolant_flow: float | None
    status: str


def generate_plant(now: datetime | None = None) -> PlantSnapshot:
    """Build a reproducible synthetic plant. `now` is the exclusive end of the series."""
    clock = _as_utc(now or datetime.now(UTC)).replace(minute=0, second=0, microsecond=0)
    rng = Random(RNG_SEED)
    equipment = tuple(_equipment_drafts())
    by_code = {item.code: item for item in equipment}
    readings = _generate_readings(equipment, clock, rng)
    alarms = _generate_alarms(by_code, readings, clock)
    maintenance = _maintenance_drafts(by_code, clock)
    work_orders = _work_order_drafts(by_code, clock)
    return PlantSnapshot(
        generated_at=clock,
        equipment=equipment,
        readings=tuple(readings),
        alarms=tuple(alarms),
        maintenance=tuple(maintenance),
        work_orders=tuple(work_orders),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _equipment_drafts() -> list[EquipmentDraft]:
    drafts: list[EquipmentDraft] = []
    for row in load_equipment_catalog():
        drafts.append(
            EquipmentDraft(
                id=stable_uuid("equipment", row.code),
                code=row.code,
                name=row.name,
                equipment_type=row.equipment_type,
                model=row.model,
                manufacturer=row.manufacturer,
                location=row.location,
                status=row.status,
                installed_at=datetime.fromisoformat(row.installed_at).astimezone(UTC),
                attributes=dict(row.attributes),
            )
        )
    return drafts


def _hourly_range(now: datetime) -> list[datetime]:
    start = now - timedelta(days=HISTORY_DAYS)
    timestamps: list[datetime] = []
    cursor = start
    while cursor < now:
        timestamps.append(cursor)
        cursor += timedelta(hours=1)
    return timestamps


def _generate_readings(
    equipment: tuple[EquipmentDraft, ...],
    now: datetime,
    rng: Random,
) -> list[ReadingDraft]:
    timestamps = _hourly_range(now)
    readings: list[ReadingDraft] = []
    for asset in equipment:
        for ts in timestamps:
            values = _reading_values(asset.code, ts, now, rng)
            readings.append(
                ReadingDraft(
                    id=stable_uuid("reading", asset.code, ts.isoformat()),
                    equipment_id=asset.id,
                    equipment_code=asset.code,
                    timestamp=ts,
                    temperature=values.temperature,
                    vibration=values.vibration,
                    pressure=values.pressure,
                    rpm=values.rpm,
                    power_consumption=values.power_consumption,
                    coolant_flow=values.coolant_flow,
                    status=values.status,
                )
            )
    return readings


def _reading_values(code: str, ts: datetime, now: datetime, rng: Random) -> ReadingValues:
    if code == CNC_CODE:
        return _cnc_values(ts, now, rng)
    if code == "PUMP-AX200":
        return ReadingValues(
            temperature=_r(42.0 + rng.uniform(-1.0, 1.0)),
            vibration=_r(1.8 + rng.uniform(-0.15, 0.2), 3),
            pressure=_r(6.2 + rng.uniform(-0.1, 0.1), 3),
            rpm=_r(1750 + rng.uniform(-12, 12), 1),
            power_consumption=_r(18.4 + rng.uniform(-0.4, 0.4)),
            coolant_flow=None,
            status=SensorStatus.RUNNING.value,
        )
    if code == "CONVEYOR-B17":
        return ReadingValues(
            temperature=_r(31.0 + rng.uniform(-0.8, 0.8)),
            vibration=_r(0.9 + rng.uniform(-0.08, 0.08), 3),
            pressure=_r(0.0, 3),
            rpm=_r(420 + rng.uniform(-8, 8), 1),
            power_consumption=_r(4.1 + rng.uniform(-0.2, 0.2)),
            coolant_flow=None,
            status=SensorStatus.RUNNING.value,
        )
    if code == "PRESS-HYD-03":
        return ReadingValues(
            temperature=_r(47.0 + rng.uniform(-1.2, 1.2)),
            vibration=_r(1.1 + rng.uniform(-0.1, 0.1), 3),
            pressure=_r(165.0 + rng.uniform(-4.0, 4.0), 1),
            rpm=_r(0.0, 1),
            power_consumption=_r(22.0 + rng.uniform(-0.6, 0.6)),
            coolant_flow=None,
            status=SensorStatus.RUNNING.value,
        )
    return ReadingValues(
        temperature=_r(68.0 + rng.uniform(-1.5, 1.5)),
        vibration=_r(2.4 + rng.uniform(-0.12, 0.12), 3),
        pressure=_r(7.4 + rng.uniform(-0.15, 0.15), 3),
        rpm=_r(2960 + rng.uniform(-20, 20), 1),
        power_consumption=_r(55.0 + rng.uniform(-1.2, 1.2)),
        coolant_flow=None,
        status=SensorStatus.RUNNING.value,
    )


def _cnc_values(ts: datetime, now: datetime, rng: Random) -> ReadingValues:
    window_start = now - timedelta(days=LOOKBACK_DAYS)
    noise_t = rng.uniform(-0.45, 0.45)
    noise_c = rng.uniform(-0.08, 0.08)
    if ts < window_start:
        coolant = 12.05 + noise_c
        temperature = 58.2 + noise_t
    else:
        progress = (ts - window_start) / timedelta(days=LOOKBACK_DAYS)
        coolant = 11.8 - progress * 6.1 + noise_c
        temperature = 58.4 + progress * 23.6 + noise_t

    days_before_end = (now.date() - ts.date()).days
    if 1 <= days_before_end <= CNC_HIGH_TEMP_SPIKE_DAYS and ts.hour == 16:
        temperature = max(temperature, 80.6 + rng.uniform(0.0, 0.8))
    if 1 <= days_before_end <= CNC_ALARM_DAYS and ts.hour == 15:
        temperature = max(temperature, 81.4 + rng.uniform(0.0, 1.1))
        coolant = min(coolant, 6.1)

    status = (
        SensorStatus.ALARM.value
        if temperature >= TEMP_HIGH_THRESHOLD_C
        else SensorStatus.RUNNING.value
    )
    return ReadingValues(
        temperature=_r(temperature),
        vibration=_r(1.35 + rng.uniform(-0.08, 0.08), 3),
        pressure=_r(6.8 + rng.uniform(-0.12, 0.12), 3),
        rpm=_r(8200 + rng.uniform(-40, 40), 1),
        power_consumption=_r(14.2 + rng.uniform(-0.35, 0.35)),
        coolant_flow=_r(coolant, 2),
        status=status,
    )


def _generate_alarms(
    by_code: dict[str, EquipmentDraft],
    readings: list[ReadingDraft],
    now: datetime,
) -> list[AlarmDraft]:
    alarms: list[AlarmDraft] = []
    cnc = by_code[CNC_CODE]
    for reading in readings:
        if reading.equipment_code != CNC_CODE:
            continue
        days_before_end = (now.date() - reading.timestamp.date()).days
        if 1 <= days_before_end <= CNC_ALARM_DAYS and reading.timestamp.hour == 15:
            alarms.append(
                AlarmDraft(
                    id=stable_uuid(
                        "alarm", CNC_CODE, TEMP_HIGH_CODE, reading.timestamp.isoformat()
                    ),
                    equipment_id=cnc.id,
                    equipment_code=CNC_CODE,
                    timestamp=reading.timestamp,
                    code=TEMP_HIGH_CODE,
                    severity=AlarmSeverity.CRITICAL.value,
                    message=(
                        f"Coolant/spindle temperature {reading.temperature:.1f} C exceeded "
                        f"{TEMP_HIGH_THRESHOLD_C:.0f} C threshold. Coolant flow "
                        f"{(reading.coolant_flow or 0.0):.2f} L/min."
                    ),
                    acknowledged_at=None,
                    cleared_at=None,
                )
            )

    pump = by_code["PUMP-AX200"]
    pump_alarm_at = now - timedelta(days=21, hours=4)
    pump_alarm_at = pump_alarm_at.replace(minute=0, second=0, microsecond=0)
    alarms.append(
        AlarmDraft(
            id=stable_uuid("alarm", "PUMP-AX200", "VIB_HIGH", pump_alarm_at.isoformat()),
            equipment_id=pump.id,
            equipment_code="PUMP-AX200",
            timestamp=pump_alarm_at,
            code="VIB_HIGH",
            severity=AlarmSeverity.WARNING.value,
            message="Brief vibration excursion on PUMP-AX200. Cleared after 12 minutes.",
            acknowledged_at=pump_alarm_at + timedelta(minutes=6),
            cleared_at=pump_alarm_at + timedelta(minutes=12),
        )
    )
    return alarms


def _maintenance_drafts(
    by_code: dict[str, EquipmentDraft], now: datetime
) -> list[MaintenanceDraft]:
    drafts: list[MaintenanceDraft] = []
    for row in load_maintenance_catalog():
        asset = by_code[row.equipment_code]
        performed_at = _offset_at(now, row.offset_days, row.hour_utc)
        next_due_at = (
            _offset_at(now, row.next_due_offset_days, 9)
            if row.next_due_offset_days is not None
            else None
        )
        drafts.append(
            MaintenanceDraft(
                id=stable_uuid(
                    "maintenance", row.equipment_code, row.title, performed_at.isoformat()
                ),
                equipment_id=asset.id,
                equipment_code=row.equipment_code,
                performed_at=performed_at,
                maintenance_type=row.maintenance_type,
                title=row.title,
                description=row.description,
                technician=row.technician,
                result=row.result,
                next_due_at=next_due_at,
            )
        )
    return drafts


def _work_order_drafts(by_code: dict[str, EquipmentDraft], now: datetime) -> list[WorkOrderDraft]:
    drafts: list[WorkOrderDraft] = []
    for row in load_work_order_catalog():
        asset = by_code[row.equipment_code]
        created_at = _offset_at(now, row.created_offset_days, 8)
        completed_at = (
            _offset_at(now, row.completed_offset_days, 15)
            if row.completed_offset_days is not None
            else None
        )
        drafts.append(
            WorkOrderDraft(
                id=stable_uuid("work_order", row.number),
                equipment_id=asset.id,
                equipment_code=row.equipment_code,
                number=row.number,
                title=row.title,
                description=row.description,
                status=row.status,
                priority=row.priority,
                created_at=created_at,
                updated_at=completed_at or created_at,
                completed_at=completed_at,
            )
        )
    return drafts


def _offset_at(now: datetime, offset_days: int, hour_utc: int) -> datetime:
    point = now + timedelta(days=offset_days)
    return point.replace(hour=hour_utc, minute=0, second=0, microsecond=0)


def _r(value: float, digits: int = 2) -> float:
    return round(value, digits)
