"""MCP tool registry and gateway tests. No PostgreSQL required."""

import asyncio

import pytest
from forgeflow.domain.schemas import EquipmentOut
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK, TEMP_HIGH_CODE
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.errors import (
    NotFoundError,
    ToolAuthorizationError,
    ToolTimeoutError,
    ToolValidationError,
)
from forgeflow.mcp.authz import DenyAllAuthorizer
from forgeflow.mcp.registry import ToolRegistry
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.mcp.schemas import (
    GET_ALARM_HISTORY,
    GET_EQUIPMENT,
    GET_MAINTENANCE_HISTORY,
    GET_SENSOR_HISTORY,
)
from forgeflow.services.snapshot import InMemoryIndustrialReader


def _reader() -> InMemoryIndustrialReader:
    return InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))


@pytest.mark.asyncio
async def test_registry_get_equipment_cnc() -> None:
    registry = ToolRegistry(_reader())
    payload = await registry.invoke(GET_EQUIPMENT, {"equipment_id": CNC_CODE})
    assert payload["code"] == CNC_CODE
    assert payload["model"] == "FX-400"


@pytest.mark.asyncio
async def test_registry_unknown_equipment() -> None:
    registry = ToolRegistry(_reader())
    with pytest.raises(NotFoundError):
        await registry.invoke(GET_EQUIPMENT, {"equipment_id": "NO-SUCH"})


@pytest.mark.asyncio
async def test_registry_rejects_invalid_limit() -> None:
    registry = ToolRegistry(_reader())
    with pytest.raises(ToolValidationError):
        await registry.invoke(
            GET_SENSOR_HISTORY,
            {"equipment_id": CNC_CODE, "limit": 0},
        )


@pytest.mark.asyncio
async def test_registry_timeout() -> None:
    class SlowReader(InMemoryIndustrialReader):
        async def get_equipment(self, code: str) -> EquipmentOut:
            await asyncio.sleep(1)
            return await super().get_equipment(code)

    registry = ToolRegistry(SlowReader(generate_plant(now=DEMO_CLOCK)), timeout_seconds=0.05)
    with pytest.raises(ToolTimeoutError):
        await registry.invoke(GET_EQUIPMENT, {"equipment_id": CNC_CODE})


@pytest.mark.asyncio
async def test_registry_authorization_stub() -> None:
    registry = ToolRegistry(_reader(), authorizer=DenyAllAuthorizer())
    with pytest.raises(ToolAuthorizationError):
        await registry.invoke(GET_EQUIPMENT, {"equipment_id": CNC_CODE})


@pytest.mark.asyncio
async def test_gateway_lists_required_tools() -> None:
    gateway = build_tool_gateway(_reader())
    tools = await gateway.list_tools()
    names = {item.name for item in tools}
    assert names == {
        GET_EQUIPMENT,
        GET_SENSOR_HISTORY,
        GET_ALARM_HISTORY,
        GET_MAINTENANCE_HISTORY,
    }
    by_name = {item.name: item for item in tools}
    assert by_name[GET_EQUIPMENT].server == "forgeflow-equipment"
    assert by_name[GET_MAINTENANCE_HISTORY].server == "forgeflow-maintenance"
    assert "equipment_id" in by_name[GET_EQUIPMENT].input_schema.get("properties", {})


@pytest.mark.asyncio
async def test_gateway_history_tools_for_cnc() -> None:
    gateway = build_tool_gateway(_reader())
    window = {
        "equipment_id": CNC_CODE,
        "start": "2026-08-04T12:00:00+00:00",
        "end": DEMO_CLOCK.isoformat(),
    }
    telemetry = await gateway.call(GET_SENSOR_HISTORY, window)
    alarms = await gateway.call(GET_ALARM_HISTORY, window)
    maintenance = await gateway.call(GET_MAINTENANCE_HISTORY, {"equipment_id": CNC_CODE})
    assert telemetry["count"] > 100
    assert any(item["code"] == TEMP_HIGH_CODE for item in alarms["items"])
    assert any(item["title"] == "Cooling system inspection" for item in maintenance["items"])
