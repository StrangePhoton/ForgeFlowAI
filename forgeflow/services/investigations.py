"""Investigation HTTP store. Memory in tests; PostgreSQL for the Compose demo."""

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from forgeflow.agent.models import InvestigationResult, PendingApproval
from forgeflow.domain.models import ApprovalRequest, InvestigationRecord


class InvestigationStore(Protocol):
    async def get(self, investigation_id: str) -> InvestigationResult | None: ...

    async def list_results(self) -> list[InvestigationResult]: ...

    async def put(self, result: InvestigationResult) -> None: ...

    async def pending_approvals(self) -> list[PendingApproval]: ...


class MemoryInvestigationStore:
    def __init__(self) -> None:
        self._items: dict[str, InvestigationResult] = {}
        self._order: list[str] = []

    async def get(self, investigation_id: str) -> InvestigationResult | None:
        return self._items.get(investigation_id)

    async def list_results(self) -> list[InvestigationResult]:
        return [self._items[key] for key in reversed(self._order) if key in self._items]

    async def put(self, result: InvestigationResult) -> None:
        investigation_id = result.investigation_id
        if not investigation_id:
            return
        if investigation_id not in self._items:
            self._order.append(investigation_id)
        self._items[investigation_id] = result

    async def pending_approvals(self) -> list[PendingApproval]:
        pending: list[PendingApproval] = []
        for item in await self.list_results():
            if item.status == "awaiting_approval" and item.approval is not None:
                pending.append(item.approval)
        return pending


class PostgresInvestigationStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, investigation_id: str) -> InvestigationResult | None:
        parsed = _as_uuid(investigation_id)
        if parsed is None:
            return None
        async with self._session_factory() as session:
            row = await session.get(InvestigationRecord, parsed)
            if row is None:
                return None
            return InvestigationResult.model_validate(row.payload)

    async def list_results(self) -> list[InvestigationResult]:
        async with self._session_factory() as session:
            stmt = select(InvestigationRecord).order_by(InvestigationRecord.updated_at.desc())
            rows = (await session.scalars(stmt)).all()
            return [InvestigationResult.model_validate(row.payload) for row in rows]

    async def put(self, result: InvestigationResult) -> None:
        investigation_id = result.investigation_id
        parsed = _as_uuid(investigation_id or "")
        if parsed is None:
            return
        now = datetime.now(UTC)
        payload = result.model_dump(mode="json")
        async with self._session_factory() as session:
            row = await session.get(InvestigationRecord, parsed)
            if row is None:
                session.add(
                    InvestigationRecord(
                        id=parsed,
                        status=result.status,
                        payload=payload,
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                row.status = result.status
                row.payload = payload
                row.updated_at = now
            await _sync_approval_row(session, parsed, result, now)
            await session.commit()

    async def pending_approvals(self) -> list[PendingApproval]:
        pending: list[PendingApproval] = []
        for item in await self.list_results():
            if item.status == "awaiting_approval" and item.approval is not None:
                pending.append(item.approval)
        return pending


def _as_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


async def _sync_approval_row(
    session: AsyncSession,
    investigation_id: UUID,
    result: InvestigationResult,
    now: datetime,
) -> None:
    stmt = select(ApprovalRequest).where(ApprovalRequest.investigation_id == investigation_id)
    rows = (await session.scalars(stmt)).all()
    if result.status == "awaiting_approval" and result.approval is not None:
        proposal = dict(result.approval.proposal)
        if rows:
            current = rows[0]
            current.status = "pending"
            current.proposal = proposal
            current.tool_name = result.approval.tool_name
            current.resolved_at = None
            current.resolution = None
            return
        session.add(
            ApprovalRequest(
                investigation_id=investigation_id,
                thread_id=str(investigation_id),
                tool_name=result.approval.tool_name,
                proposal=proposal,
                status="pending",
                created_at=now,
            )
        )
        return
    resolution_status = "approved" if result.work_order is not None else result.status
    for row in rows:
        if row.status != "pending":
            continue
        row.status = resolution_status
        row.resolved_at = now
        row.resolution = {"status": result.status}
