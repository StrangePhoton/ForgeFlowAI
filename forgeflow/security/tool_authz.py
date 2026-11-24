"""Tool-layer RBAC. Complements ApprovalGate; the model cannot grant tools."""

from typing import Any

from forgeflow.errors import ToolAuthorizationError
from forgeflow.mcp.authz import ToolAuthorizer
from forgeflow.mcp.schemas import CREATE_WORK_ORDER
from forgeflow.security.principal import Principal

READ_TOOLS = frozenset(
    {
        "get_equipment",
        "get_sensor_history",
        "get_alarm_history",
        "get_maintenance_history",
        "search_documentation",
    }
)
WRITE_TOOLS = frozenset({CREATE_WORK_ORDER})


class RoleToolAuthorizer:
    """Deny tools the caller's role is not allowed to invoke."""

    def __init__(self, principal: Principal) -> None:
        self._principal = principal

    def authorize(self, tool_name: str, arguments: dict[str, Any]) -> None:
        del arguments
        if tool_name in WRITE_TOOLS:
            if not self._principal.allows("tools:write"):
                raise ToolAuthorizationError(
                    f"{tool_name} is not allowed for role {self._principal.role}"
                )
            return
        if tool_name in READ_TOOLS:
            if not self._principal.allows("tools:read"):
                raise ToolAuthorizationError(
                    f"{tool_name} is not allowed for role {self._principal.role}"
                )
            return
        raise ToolAuthorizationError(f"Unknown tool {tool_name} is not authorized")


class CompositeAuthorizer:
    """Run every authorizer. First denial wins."""

    def __init__(self, *authorizers: ToolAuthorizer) -> None:
        self._authorizers = authorizers

    def authorize(self, tool_name: str, arguments: dict[str, Any]) -> None:
        for authorizer in self._authorizers:
            authorizer.authorize(tool_name, arguments)
