"""CNC-042 and plant-wide synthetic scenario tests. No database required."""

from datetime import timedelta
from statistics import mean

from forgeflow.domain.seed.constants import (
    CNC_ALARM_DAYS,
    CNC_CODE,
    CNC_HIGH_TEMP_SPIKE_DAYS,
    COOLING_INSPECTION_INTERVAL_DAYS,
    DEMO_CLOCK,
    HIGH_TEMP_ANOMALY_C,
    LOOKBACK_DAYS,
    TEMP_HIGH_CODE,
)
from forgeflow.domain.seed.generate import generate_plant

SEED_NOW = DEMO_CLOCK
REQUIRED_CODES = {
    "CNC-042",
    "PUMP-AX200",
    "CONVEYOR-B17",
    "PRESS-HYD-03",
    "COMPRESSOR-C09",
}


def test_plant_contains_required_equipment() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    assert {item.code for item in snapshot.equipment} == REQUIRED_CODES
    cnc = snapshot.equipment_by_code(CNC_CODE)
    assert cnc.model == "FX-400"
    assert cnc.status == "alarm"
    assert cnc.attributes["coolant_loop"] is True


def test_cnc_temperature_rises_over_last_30_days() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    readings = snapshot.readings_for(CNC_CODE)
    recent = [
        row.temperature
        for row in readings
        if SEED_NOW - timedelta(days=7) <= row.timestamp < SEED_NOW
    ]
    baseline = [
        row.temperature
        for row in readings
        if SEED_NOW - timedelta(days=LOOKBACK_DAYS) <= row.timestamp < SEED_NOW - timedelta(days=23)
    ]
    assert recent
    assert baseline
    assert mean(recent) > mean(baseline) + 8


def test_cnc_coolant_flow_declines() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    readings = [row for row in snapshot.readings_for(CNC_CODE) if row.coolant_flow is not None]
    recent = [
        row.coolant_flow
        for row in readings
        if row.coolant_flow is not None and SEED_NOW - timedelta(days=7) <= row.timestamp < SEED_NOW
    ]
    baseline = [
        row.coolant_flow
        for row in readings
        if row.coolant_flow is not None
        and SEED_NOW - timedelta(days=LOOKBACK_DAYS)
        <= row.timestamp
        < SEED_NOW - timedelta(days=23)
    ]
    assert mean(recent) < mean(baseline) - 3


def test_cnc_has_expected_temp_high_alarms() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    window_start = SEED_NOW - timedelta(days=LOOKBACK_DAYS)
    alarms = [
        row
        for row in snapshot.alarms_for(CNC_CODE)
        if row.code == TEMP_HIGH_CODE and window_start <= row.timestamp < SEED_NOW
    ]
    assert len(alarms) == CNC_ALARM_DAYS
    assert all(row.severity == "critical" for row in alarms)


def test_cnc_has_high_temperature_anomalies() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    window_start = SEED_NOW - timedelta(days=LOOKBACK_DAYS)
    high = [
        row
        for row in snapshot.readings_for(CNC_CODE)
        if window_start <= row.timestamp < SEED_NOW and row.temperature >= HIGH_TEMP_ANOMALY_C
    ]
    assert len(high) >= CNC_HIGH_TEMP_SPIKE_DAYS


def test_cnc_cooling_inspection_is_overdue() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    cooling = next(
        row
        for row in snapshot.maintenance_for(CNC_CODE)
        if row.title == "Cooling system inspection"
    )
    assert cooling.next_due_at is not None
    assert cooling.next_due_at < SEED_NOW
    assert (SEED_NOW - cooling.performed_at).days > COOLING_INSPECTION_INTERVAL_DAYS


def test_cnc_has_no_open_cooling_work_order() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    assert snapshot.work_orders_for(CNC_CODE) == ()


def test_peer_equipment_does_not_share_cnc_overheat_pattern() -> None:
    snapshot = generate_plant(now=SEED_NOW)
    for code in REQUIRED_CODES - {CNC_CODE}:
        temp_high = [row for row in snapshot.alarms_for(code) if row.code == TEMP_HIGH_CODE]
        assert temp_high == []
        cooling = [row for row in snapshot.maintenance_for(code) if "cooling" in row.title.lower()]
        assert cooling == []


def test_generation_is_deterministic() -> None:
    first = generate_plant(now=SEED_NOW)
    second = generate_plant(now=SEED_NOW)
    assert [row.id for row in first.readings] == [row.id for row in second.readings]
    assert [row.temperature for row in first.readings_for(CNC_CODE)] == [
        row.temperature for row in second.readings_for(CNC_CODE)
    ]
