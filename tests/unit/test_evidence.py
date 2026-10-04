"""Deterministic evidence evaluation for the CNC-042 scenario."""

from forgeflow.agent.evidence import evaluate_evidence
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK, TEMP_HIGH_CODE
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.mcp.schemas import (
    GET_ALARM_HISTORY,
    GET_EQUIPMENT,
    GET_MAINTENANCE_HISTORY,
    GET_SENSOR_HISTORY,
)
from forgeflow.services.snapshot import InMemoryIndustrialReader


async def _cnc_payloads() -> tuple[
    dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]
]:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(reader)
    window = {
        "equipment_id": CNC_CODE,
        "start": "2026-08-04T12:00:00+00:00",
        "end": DEMO_CLOCK.isoformat(),
    }
    equipment = await gateway.call(GET_EQUIPMENT, {"equipment_id": CNC_CODE})
    telemetry = await gateway.call(GET_SENSOR_HISTORY, window)
    alarms = await gateway.call(GET_ALARM_HISTORY, window)
    maintenance = await gateway.call(GET_MAINTENANCE_HISTORY, {"equipment_id": CNC_CODE})
    return equipment, telemetry["items"], alarms["items"], maintenance["items"]


async def test_cnc_evidence_is_sufficient() -> None:
    equipment, telemetry, alarms, maintenance = await _cnc_payloads()
    bundle = evaluate_evidence(
        equipment_code=CNC_CODE,
        equipment=equipment,
        telemetry=telemetry,
        alarms=alarms,
        maintenance=maintenance,
        as_of=DEMO_CLOCK,
    )
    assert bundle.evidence_sufficient is True
    assert bundle.temp_high_count >= 3
    statements = " ".join(item.statement for item in bundle.facts)
    assert TEMP_HIGH_CODE in statements
    assert "coolant" in statements.lower()
    assert "overdue" in statements.lower()
    assert bundle.likely_cause is not None
    assert any(item.kind == "INFERENCE" for item in bundle.inferences)
    assert any(item.kind == "RECOMMENDATION" for item in bundle.recommendations)


async def test_missing_equipment_is_insufficient() -> None:
    bundle = evaluate_evidence(
        equipment_code=None,
        equipment=None,
        telemetry=[],
        alarms=[],
        maintenance=[],
        as_of=DEMO_CLOCK,
    )
    assert bundle.evidence_sufficient is False
    assert bundle.confidence == "insufficient"
