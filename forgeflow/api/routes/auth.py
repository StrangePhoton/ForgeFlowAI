"""Login and current-principal endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from forgeflow.api.deps import AuditLogDep, PrincipalDep
from forgeflow.config import get_settings
from forgeflow.errors import AuthenticationError
from forgeflow.observability.logging import get_request_id
from forgeflow.security.accounts import authenticate_user, demo_directory
from forgeflow.security.roles import permissions_for
from forgeflow.security.tokens import issue_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    username: str
    role: str
    permissions: list[str]


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, audit: AuditLogDep, request: Request) -> TokenResponse:
    settings = get_settings()
    if settings.persist_workflow:
        async with request.app.state.database.session_factory() as session:
            principal = await authenticate_user(session, body.username, body.password)
    else:
        principal = demo_directory().authenticate(body.username, body.password)
    if principal is None:
        await audit.record(
            "login_failure",
            status="denied",
            username=body.username,
            request_id=get_request_id(),
        )
        raise AuthenticationError("Invalid username or password")
    token = issue_token(principal, settings)
    await audit.record(
        "login_success",
        status="ok",
        username=principal.username,
        role=principal.role,
        actor_id=principal.user_id,
        request_id=get_request_id(),
    )
    return TokenResponse(access_token=token, username=principal.username, role=principal.role)


@router.get("/me", response_model=MeResponse)
async def me(principal: PrincipalDep) -> MeResponse:
    return MeResponse(
        user_id=str(principal.user_id),
        username=principal.username,
        role=principal.role,
        permissions=sorted(permissions_for(principal.role)),
    )
