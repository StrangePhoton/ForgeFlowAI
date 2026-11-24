"""Investigation workflow and human-approval endpoints."""

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Request

from forgeflow.agent.models import (
    ApprovalDecision,
    InvestigationRequest,
    InvestigationResult,
    PendingApproval,
)
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.runner import InvestigationRunner
from forgeflow.api.deps import (
    AuditLogDep,
    IndustrialServiceDep,
    LLMProviderDep,
    NeedApprovalDecide,
    NeedApprovalRead,
    NeedInvestigationCreate,
    NeedInvestigationRead,
)
from forgeflow.config import get_settings
from forgeflow.errors import NotFoundError, ToolAuthorizationError
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.observability.logging import get_request_id
from forgeflow.retrieval.search.hits import DocumentSearcher
from forgeflow.security.audit import AuditLog, PostgresAuditLog
from forgeflow.security.principal import Principal
from forgeflow.security.tool_authz import CompositeAuthorizer, RoleToolAuthorizer
from forgeflow.services.investigations import InvestigationStore, MemoryInvestigationStore

router = APIRouter(tags=["investigations"])


@router.post("/investigations", response_model=InvestigationResult)
async def create_investigation(
    body: InvestigationRequest,
    request: Request,
    service: IndustrialServiceDep,
    llm: LLMProviderDep,
    audit: AuditLogDep,
    principal: NeedInvestigationCreate,
) -> InvestigationResult:
    runner = _runner(request, service, llm, principal)
    result = await runner.run(body.request)
    await _store(request).put(result)
    await audit.record(
        "investigation_started",
        username=principal.username,
        role=principal.role,
        actor_id=principal.user_id,
        request_id=get_request_id(),
        investigation_id=result.investigation_id,
        resource_type="investigation",
        resource_id=result.investigation_id,
        details={"status": result.status},
    )
    if result.status == "awaiting_approval":
        await audit.record(
            "approval_requested",
            username=principal.username,
            role=principal.role,
            actor_id=principal.user_id,
            request_id=get_request_id(),
            investigation_id=result.investigation_id,
            tool_name="create_work_order",
        )
    return result


@router.get("/investigations", response_model=list[InvestigationResult])
async def list_investigations(
    request: Request,
    _principal: NeedInvestigationRead,
) -> list[InvestigationResult]:
    return await _store(request).list_results()


@router.get("/investigations/{investigation_id}", response_model=InvestigationResult)
async def get_investigation(
    investigation_id: str,
    request: Request,
    _principal: NeedInvestigationRead,
) -> InvestigationResult:
    stored = await _store(request).get(investigation_id)
    if stored is None:
        raise NotFoundError(f"Investigation {investigation_id} was not found")
    return stored


@router.get("/approvals", response_model=list[PendingApproval])
async def list_approvals(
    request: Request,
    _principal: NeedApprovalRead,
) -> list[PendingApproval]:
    return await _store(request).pending_approvals()


@router.post("/approvals/{investigation_id}/approve", response_model=InvestigationResult)
async def approve_investigation(
    investigation_id: str,
    request: Request,
    service: IndustrialServiceDep,
    llm: LLMProviderDep,
    audit: AuditLogDep,
    principal: NeedApprovalDecide,
    body: ApprovalDecision | None = None,
) -> InvestigationResult:
    decision = body or ApprovalDecision(decision="approve")
    decision = decision.model_copy(update={"decision": "approve"})
    return await _resume(investigation_id, request, service, llm, principal, audit, decision)


@router.post("/approvals/{investigation_id}/reject", response_model=InvestigationResult)
async def reject_investigation(
    investigation_id: str,
    request: Request,
    service: IndustrialServiceDep,
    llm: LLMProviderDep,
    audit: AuditLogDep,
    principal: NeedApprovalDecide,
    body: ApprovalDecision | None = None,
) -> InvestigationResult:
    decision = body or ApprovalDecision(decision="reject")
    decision = decision.model_copy(update={"decision": "reject"})
    return await _resume(investigation_id, request, service, llm, principal, audit, decision)


async def _resume(
    investigation_id: str,
    request: Request,
    service: Any,
    llm: LLMProvider,
    principal: Principal,
    audit: AuditLog | PostgresAuditLog,
    body: ApprovalDecision,
) -> InvestigationResult:
    current = await _store(request).get(investigation_id)
    if current is None or current.status != "awaiting_approval":
        raise NotFoundError(f"No pending approval for {investigation_id}")
    if body.decision == "approve" and current.approval is None:
        raise ToolAuthorizationError("Protected write requires human approval")
    payload: dict[str, Any] = {
        "decision": body.decision,
        "reason": body.reason,
        "title": body.title,
        "description": body.description,
        "priority": body.priority,
    }
    runner = _runner(request, service, llm, principal)
    result = await runner.resume(investigation_id, payload)
    await _store(request).put(result)
    await audit.record(
        "approval_decided",
        username=principal.username,
        role=principal.role,
        actor_id=principal.user_id,
        request_id=get_request_id(),
        investigation_id=investigation_id,
        tool_name="create_work_order",
        details={"decision": body.decision},
    )
    if result.work_order is not None:
        await audit.record(
            "work_order_created",
            username=principal.username,
            role=principal.role,
            actor_id=principal.user_id,
            request_id=get_request_id(),
            investigation_id=investigation_id,
            tool_name="create_work_order",
            resource_type="work_order",
            resource_id=str(result.work_order.id),
        )
    return result


def _runner(
    request: Request, service: Any, llm: LLMProvider, principal: Principal
) -> InvestigationRunner:
    settings = get_settings()
    gate = cast(ApprovalGate, request.app.state.approval_gate)
    searcher = cast(DocumentSearcher, request.app.state.document_searcher)
    gateway = build_tool_gateway(
        service,
        documents=searcher,
        timeout_seconds=settings.mcp_tool_timeout_seconds,
        authorizer=CompositeAuthorizer(RoleToolAuthorizer(principal), gate),
    )
    as_of = settings.investigation_as_of or datetime.now(UTC)
    return InvestigationRunner(
        tools=gateway,
        llm=llm,
        as_of=as_of,
        checkpointer=request.app.state.checkpointer,
        approval_gate=gate,
    )


def _store(request: Request) -> InvestigationStore:
    store = getattr(request.app.state, "investigation_store", None)
    if store is None:
        store = MemoryInvestigationStore()
        request.app.state.investigation_store = store
    return cast(InvestigationStore, store)
