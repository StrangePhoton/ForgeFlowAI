"""Maintenance MCP server: inspection and repair history."""

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from forgeflow import __version__
from forgeflow.errors import ForgeFlowError
from forgeflow.mcp.registry import ToolRegistry
from forgeflow.mcp.schemas import GET_MAINTENANCE_HISTORY, MaintenanceHistoryResult


def create_maintenance_server(registry: ToolRegistry) -> MCPServer[Any]:
    """Build the maintenance MCP server around a shared tool registry."""
    server: MCPServer[Any] = MCPServer(
        name="forgeflow-maintenance",
        instructions="Read-only maintenance history tools.",
        version=__version__,
    )

    @server.tool(
        name=GET_MAINTENANCE_HISTORY,
        description="Return maintenance records for one equipment item.",
        structured_output=True,
    )
    async def get_maintenance_history(equipment_id: str) -> MaintenanceHistoryResult:
        try:
            payload = await registry.invoke(GET_MAINTENANCE_HISTORY, {"equipment_id": equipment_id})
        except ForgeFlowError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc
        return MaintenanceHistoryResult.model_validate(payload)

    return server
