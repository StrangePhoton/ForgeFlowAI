"""Maintenance MCP server: inspection and repair history."""

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from forgeflow import __version__
from forgeflow.domain.schemas import WorkOrderOut
from forgeflow.errors import ForgeFlowError
from forgeflow.mcp.registry import ToolRegistry
from forgeflow.mcp.schemas import (
    CREATE_WORK_ORDER,
    GET_MAINTENANCE_HISTORY,
    MaintenanceHistoryResult,
)


def create_maintenance_server(registry: ToolRegistry) -> MCPServer[Any]:
    """Build the maintenance MCP server around a shared tool registry."""
    server: MCPServer[Any] = MCPServer(
        name="forgeflow-maintenance",
        instructions="Maintenance history and protected work-order writes.",
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

    @server.tool(
        name=CREATE_WORK_ORDER,
        description="Create a maintenance work order. Protected writes require human approval.",
        structured_output=True,
    )
    async def create_work_order(
        equipment_id: str,
        title: str,
        description: str,
        idempotency_key: str,
        priority: str = "high",
        source_investigation_id: str | None = None,
    ) -> WorkOrderOut:
        arguments: dict[str, Any] = {
            "equipment_id": equipment_id,
            "title": title,
            "description": description,
            "priority": priority,
            "idempotency_key": idempotency_key,
        }
        if source_investigation_id is not None:
            arguments["source_investigation_id"] = source_investigation_id
        try:
            payload = await registry.invoke(CREATE_WORK_ORDER, arguments)
        except ForgeFlowError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc
        return WorkOrderOut.model_validate(payload)

    return server
