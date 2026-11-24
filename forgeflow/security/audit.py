"""In-process security audit log. Secrets are never stored."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class AuditEvent:
    id: UUID
    occurred_at: datetime
    event_type: str
    status: str
    username: str | None = None
    role: str | None = None
    actor_id: UUID | None = None
    tool_name: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    request_id: str | None = None
    investigation_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "occurred_at": self.occurred_at.isoformat(),
            "event_type": self.event_type,
            "status": self.status,
            "username": self.username,
            "role": self.role,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "tool_name": self.tool_name,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "request_id": self.request_id,
            "investigation_id": self.investigation_id,
            "details": dict(self.details),
        }


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        event_type: str,
        *,
        status: str = "ok",
        username: str | None = None,
        role: str | None = None,
        actor_id: UUID | None = None,
        tool_name: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        request_id: str | None = None,
        investigation_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=uuid4(),
            occurred_at=datetime.now(UTC),
            event_type=event_type,
            status=status,
            username=username,
            role=role,
            actor_id=actor_id,
            tool_name=tool_name,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            investigation_id=investigation_id,
            details=dict(details or {}),
        )
        self._events.append(event)
        return event

    def list(
        self,
        *,
        event_type: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        items = list(reversed(self._events))
        if event_type:
            items = [item for item in items if item.event_type == event_type]
        if tool_name:
            items = [item for item in items if item.tool_name == tool_name]
        if status:
            items = [item for item in items if item.status == status]
        return items[: max(1, min(limit, 500))]
