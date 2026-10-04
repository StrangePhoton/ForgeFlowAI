"""MCP ClientSession discovery and invocation over in-memory streams."""

import pytest
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.mcp.runtime import build_tool_gateway, in_process_mcp_session
from forgeflow.mcp.schemas import GET_EQUIPMENT, GET_MAINTENANCE_HISTORY
from forgeflow.services.snapshot import InMemoryIndustrialReader
from mcp.types import CallToolResult


@pytest.mark.asyncio
async def test_mcp_client_discovers_and_invokes_equipment_tools() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(reader)
    async with in_process_mcp_session(gateway.equipment_server) as session:
        listed = await session.list_tools()
        names = {tool.name for tool in listed.tools}
        assert GET_EQUIPMENT in names
        result = await session.call_tool(GET_EQUIPMENT, {"equipment_id": CNC_CODE})
        assert isinstance(result, CallToolResult)
        assert result.is_error is False
        payload = result.structured_content
        assert isinstance(payload, dict)
        assert payload["code"] == CNC_CODE
        assert payload["model"] == "FX-400"


@pytest.mark.asyncio
async def test_mcp_client_invokes_maintenance_tool() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(reader)
    async with in_process_mcp_session(gateway.maintenance_server) as session:
        listed = await session.list_tools()
        names = {tool.name for tool in listed.tools}
        assert GET_MAINTENANCE_HISTORY in names
        result = await session.call_tool(GET_MAINTENANCE_HISTORY, {"equipment_id": CNC_CODE})
        assert isinstance(result, CallToolResult)
        assert result.is_error is False
        payload = result.structured_content
        assert isinstance(payload, dict)
        assert payload["count"] >= 1
        titles = [item["title"] for item in payload["items"]]
        assert "Cooling system inspection" in titles
