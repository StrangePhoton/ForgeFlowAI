"""Equipment MCP server: registry, telemetry, and alarms."""

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from forgeflow import __version__
from forgeflow.domain.schemas import EquipmentOut
from forgeflow.domain.seed.constants import DEFAULT_HISTORY_LIMIT
from forgeflow.errors import ForgeFlowError
from forgeflow.mcp.registry import ToolRegistry
from forgeflow.mcp.schemas import (
    GET_ALARM_HISTORY,
    GET_EQUIPMENT,
    GET_SENSOR_HISTORY,
    AlarmHistoryResult,
    SensorHistoryResult,
)


def create_equipment_server(registry: ToolRegistry) -> MCPServer[Any]:
    """Build the equipment MCP server around a shared tool registry."""
    server: MCPServer[Any] = MCPServer(
        name="forgeflow-equipment",
        instructions="Read-only equipment, sensor history, and alarm tools.",
        version=__version__,
    )

    @server.tool(
        name=GET_EQUIPMENT,
        description="Return one equipment record by code or UUID.",
        structured_output=True,
    )
    async def get_equipment(equipment_id: str) -> EquipmentOut:
        try:
            payload = await registry.invoke(GET_EQUIPMENT, {"equipment_id": equipment_id})
        except ForgeFlowError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc
        return EquipmentOut.model_validate(payload)

    @server.tool(
        name=GET_SENSOR_HISTORY,
        description="Return sensor readings for equipment in an optional time window.",
        structured_output=True,
    )
    async def get_sensor_history(
        equipment_id: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> SensorHistoryResult:
        arguments: dict[str, Any] = {"equipment_id": equipment_id, "limit": limit}
        if start is not None:
            arguments["start"] = start
        if end is not None:
            arguments["end"] = end
        try:
            payload = await registry.invoke(GET_SENSOR_HISTORY, arguments)
        except ForgeFlowError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc
        return SensorHistoryResult.model_validate(payload)

    @server.tool(
        name=GET_ALARM_HISTORY,
        description="Return alarms for equipment in an optional time window.",
        structured_output=True,
    )
    async def get_alarm_history(
        equipment_id: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> AlarmHistoryResult:
        arguments: dict[str, Any] = {"equipment_id": equipment_id, "limit": limit}
        if start is not None:
            arguments["start"] = start
        if end is not None:
            arguments["end"] = end
        try:
            payload = await registry.invoke(GET_ALARM_HISTORY, arguments)
        except ForgeFlowError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc
        return AlarmHistoryResult.model_validate(payload)

    return server
