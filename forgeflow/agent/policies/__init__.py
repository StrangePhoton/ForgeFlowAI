"""Deterministic write-action policy. The LLM is never asked whether a write is allowed."""

from typing import Any

from forgeflow.errors import ToolAuthorizationError
from forgeflow.mcp.schemas import CREATE_WORK_ORDER

PROTECTED_WRITE_TOOLS = frozenset({CREATE_WORK_ORDER})


def requires_approval(action: dict[str, Any] | None) -> bool:
    if not action:
        return False
    return str(action.get("tool") or "") in PROTECTED_WRITE_TOOLS


def classify_risk(action: dict[str, Any] | None) -> str:
    if requires_approval(action):
        return "high"
    return "low"


class ApprovalGate:
    """Grants create_work_order only after a recorded human approval."""

    def __init__(self) -> None:
        self._granted: set[str] = set()

    def grant(self, idempotency_key: str) -> None:
        self._granted.add(idempotency_key)

    def authorize(self, tool_name: str, arguments: dict[str, Any]) -> None:
        if tool_name not in PROTECTED_WRITE_TOOLS:
            return
        key = str(arguments.get("idempotency_key") or "")
        if key not in self._granted:
            raise ToolAuthorizationError("create_work_order requires human approval")
