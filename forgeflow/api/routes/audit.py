"""Inspect recorded security and workflow events."""

from typing import Any

from fastapi import APIRouter, Query

from forgeflow.api.deps import AuditLogDep, NeedAuditRead

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[dict[str, Any]])
async def list_audit_events(
    audit: AuditLogDep,
    _principal: NeedAuditRead,
    event_type: str | None = None,
    tool_name: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    events = await audit.list(
        event_type=event_type, tool_name=tool_name, status=status, limit=limit
    )
    return [item.as_dict() for item in events]
