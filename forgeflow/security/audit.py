"""Security audit log. Secrets are never stored."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from forgeflow.domain.models import AuditEventRow


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

    async def record(
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

    async def list(
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


class PostgresAuditLog:
    """Durable audit events. Used when FORGEFLOW_ENVIRONMENT is not test."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(
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
        async with self._session_factory() as session:
            session.add(
                AuditEventRow(
                    id=event.id,
                    occurred_at=event.occurred_at,
                    event_type=event.event_type,
                    status=event.status,
                    username=event.username,
                    role=event.role,
                    actor_id=event.actor_id,
                    tool_name=event.tool_name,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    request_id=event.request_id,
                    investigation_id=event.investigation_id,
                    details=dict(event.details),
                )
            )
            await session.commit()
        return event

    async def list(
        self,
        *,
        event_type: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        bounded = max(1, min(limit, 500))
        async with self._session_factory() as session:
            stmt = select(AuditEventRow).order_by(AuditEventRow.occurred_at.desc())
            if event_type:
                stmt = stmt.where(AuditEventRow.event_type == event_type)
            if tool_name:
                stmt = stmt.where(AuditEventRow.tool_name == tool_name)
            if status:
                stmt = stmt.where(AuditEventRow.status == status)
            stmt = stmt.limit(bounded)
            rows = (await session.scalars(stmt)).all()
        return [_event_from_row(row) for row in rows]


def _event_from_row(row: AuditEventRow) -> AuditEvent:
    return AuditEvent(
        id=row.id,
        occurred_at=row.occurred_at,
        event_type=row.event_type,
        status=row.status,
        username=row.username,
        role=row.role,
        actor_id=row.actor_id,
        tool_name=row.tool_name,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        request_id=row.request_id,
        investigation_id=row.investigation_id,
        details=dict(row.details or {}),
    )
