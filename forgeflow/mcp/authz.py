"""Deterministic tool authorization. RBAC enforcement arrives in Milestone 6."""

from typing import Any, Protocol

from forgeflow.errors import ToolAuthorizationError


class ToolAuthorizer(Protocol):
    def authorize(self, tool_name: str, arguments: dict[str, Any]) -> None: ...


class AllowAllAuthorizer:
    """Placeholder authorizer. The LLM is never asked whether a call is allowed."""

    def authorize(self, tool_name: str, arguments: dict[str, Any]) -> None:
        return None


class DenyAllAuthorizer:
    """Test double that refuses every tool call."""

    def authorize(self, tool_name: str, arguments: dict[str, Any]) -> None:
        raise ToolAuthorizationError(f"Tool {tool_name} is not authorized")
