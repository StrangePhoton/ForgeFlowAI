"""In-process MCP client over equipment and maintenance servers."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client._memory import InMemoryTransport
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError, UnexpectedToolError
from mcp.types import CallToolResult, TextContent

from forgeflow.errors import (
    ForgeFlowError,
    NotFoundError,
    ToolAuthorizationError,
    ToolTimeoutError,
    ToolValidationError,
)
from forgeflow.mcp.authz import ToolAuthorizer
from forgeflow.mcp.documentation import create_documentation_server
from forgeflow.mcp.equipment import create_equipment_server
from forgeflow.mcp.maintenance import create_maintenance_server
from forgeflow.mcp.registry import ToolRegistry
from forgeflow.mcp.schemas import (
    DOCUMENTATION_TOOLS,
    EQUIPMENT_TOOLS,
    MAINTENANCE_TOOLS,
    ToolInfo,
)
from forgeflow.retrieval.corpus import manuals_index
from forgeflow.retrieval.search.hits import DocumentSearcher
from forgeflow.services.protocols import IndustrialReader

_ERROR_TYPES: dict[str, type[ForgeFlowError]] = {
    "not_found": NotFoundError,
    "tool_validation_error": ToolValidationError,
    "tool_timeout": ToolTimeoutError,
    "tool_authorization_denied": ToolAuthorizationError,
}


class McpToolGateway:
    """Routes agent tool calls through MCP servers rather than SQLAlchemy."""

    def __init__(
        self,
        equipment: MCPServer[Any],
        maintenance: MCPServer[Any],
        documentation: MCPServer[Any],
    ) -> None:
        self._equipment = equipment
        self._maintenance = maintenance
        self._documentation = documentation

    @property
    def equipment_server(self) -> MCPServer[Any]:
        return self._equipment

    @property
    def maintenance_server(self) -> MCPServer[Any]:
        return self._maintenance

    @property
    def documentation_server(self) -> MCPServer[Any]:
        return self._documentation

    async def list_tools(self) -> list[ToolInfo]:
        listed: list[ToolInfo] = []
        for server in (self._equipment, self._maintenance, self._documentation):
            for tool in await server.list_tools():
                listed.append(
                    ToolInfo(
                        name=tool.name,
                        description=tool.description or "",
                        server=server.name,
                        input_schema=dict(tool.input_schema or {}),
                    )
                )
        return listed

    async def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        server = self._server_for(name)
        try:
            result = await server.call_tool(name, arguments or {})
        except UnexpectedToolError as exc:
            cause = exc.__cause__
            if isinstance(cause, ForgeFlowError):
                raise cause from exc
            raise ForgeFlowError(str(exc), code="tool_error", status_code=500) from exc
        except ToolError as exc:
            raise _error_from_message(str(exc)) from exc
        if not isinstance(result, CallToolResult):
            raise ForgeFlowError(
                "Unexpected MCP tool result type", code="tool_error", status_code=500
            )
        if result.is_error:
            raise _error_from_message(_result_error_text(result))
        return _structured_payload(result)

    def _server_for(self, name: str) -> MCPServer[Any]:
        if name in EQUIPMENT_TOOLS:
            return self._equipment
        if name in MAINTENANCE_TOOLS:
            return self._maintenance
        if name in DOCUMENTATION_TOOLS:
            return self._documentation
        raise ForgeFlowError(f"Unknown tool {name}", code="unknown_tool", status_code=404)


def build_tool_gateway(
    reader: IndustrialReader,
    *,
    documents: DocumentSearcher | None = None,
    timeout_seconds: float = 15.0,
    authorizer: ToolAuthorizer | None = None,
) -> McpToolGateway:
    searcher = documents if documents is not None else manuals_index()
    registry = ToolRegistry(
        reader,
        documents=searcher,
        timeout_seconds=timeout_seconds,
        authorizer=authorizer,
    )
    return McpToolGateway(
        equipment=create_equipment_server(registry),
        maintenance=create_maintenance_server(registry),
        documentation=create_documentation_server(registry),
    )


@asynccontextmanager
async def in_process_mcp_session(server: MCPServer[Any]) -> AsyncIterator[ClientSession]:
    """Connect an MCP client to a server over in-memory streams."""
    async with InMemoryTransport(server) as streams:
        read_stream, write_stream = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


def _structured_payload(result: CallToolResult) -> dict[str, Any]:
    if isinstance(result.structured_content, dict):
        return result.structured_content
    for block in result.content:
        if isinstance(block, TextContent):
            parsed: Any = json.loads(block.text)
            if isinstance(parsed, dict):
                return parsed
    raise ForgeFlowError("Tool returned no structured payload", code="tool_error", status_code=500)


def _result_error_text(result: CallToolResult) -> str:
    for block in result.content:
        if isinstance(block, TextContent) and block.text:
            return block.text
    return "tool_error: Tool call failed"


def _error_from_message(message: str) -> ForgeFlowError:
    for code, exc_type in _ERROR_TYPES.items():
        marker = f"{code}: "
        if marker in message:
            remainder = message.split(marker, 1)[1]
            return exc_type(remainder)
    if "unknown_tool: " in message:
        remainder = message.split("unknown_tool: ", 1)[1]
        return ForgeFlowError(remainder, code="unknown_tool", status_code=404)
    return ForgeFlowError(message, code="tool_error", status_code=500)
