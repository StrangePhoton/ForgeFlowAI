"""FastAPI dependencies."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.providers.factory import create_llm_provider
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.errors import AuthenticationError, ForbiddenError
from forgeflow.observability.logging import get_request_id
from forgeflow.security.audit import AuditLog
from forgeflow.security.principal import Principal
from forgeflow.security.roles import Permission
from forgeflow.security.tokens import parse_token
from forgeflow.services.industrial import IndustrialQueryService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    async with database.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_industrial_service(session: SessionDep) -> IndustrialQueryService:
    return IndustrialQueryService(session)


IndustrialServiceDep = Annotated[IndustrialQueryService, Depends(get_industrial_service)]


def get_llm_provider(request: Request) -> LLMProvider:
    provider = getattr(request.app.state, "llm_provider", None)
    if provider is None:
        provider = create_llm_provider(get_settings())
        request.app.state.llm_provider = provider
    return cast(LLMProvider, provider)


LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]


def get_audit_log(request: Request) -> AuditLog:
    log = getattr(request.app.state, "audit_log", None)
    if log is None:
        log = AuditLog()
        request.app.state.audit_log = log
    return cast(AuditLog, log)


AuditLogDep = Annotated[AuditLog, Depends(get_audit_log)]


def get_principal(request: Request, audit: AuditLogDep) -> Principal:
    header = request.headers.get("Authorization") or ""
    if not header.startswith("Bearer "):
        audit.record(
            "authorization_denied",
            status="denied",
            request_id=get_request_id(),
            details={"reason": "missing_bearer"},
        )
        raise AuthenticationError("Authentication required")
    try:
        principal = parse_token(header.removeprefix("Bearer ").strip(), get_settings())
    except AuthenticationError:
        audit.record(
            "authorization_denied",
            status="denied",
            request_id=get_request_id(),
            details={"reason": "invalid_token"},
        )
        raise
    request.state.principal = principal
    return principal


PrincipalDep = Annotated[Principal, Depends(get_principal)]


def require_permission(permission: Permission) -> object:
    def _check(principal: PrincipalDep, audit: AuditLogDep) -> Principal:
        if not principal.allows(permission):
            audit.record(
                "authorization_denied",
                status="denied",
                username=principal.username,
                role=principal.role,
                actor_id=principal.user_id,
                request_id=get_request_id(),
                details={"permission": permission},
            )
            raise ForbiddenError(f"Role {principal.role} cannot {permission}")
        return principal

    return _check


NeedEquipmentRead = Annotated[Principal, Depends(require_permission("equipment:read"))]
NeedInvestigationRead = Annotated[Principal, Depends(require_permission("investigations:read"))]
NeedInvestigationCreate = Annotated[Principal, Depends(require_permission("investigations:create"))]
NeedApprovalRead = Annotated[Principal, Depends(require_permission("approvals:read"))]
NeedApprovalDecide = Annotated[Principal, Depends(require_permission("approvals:decide"))]
NeedAuditRead = Annotated[Principal, Depends(require_permission("audit:read"))]
