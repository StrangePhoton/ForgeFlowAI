"""Investigation workflow endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter

from forgeflow.agent.models import InvestigationRequest, InvestigationResult
from forgeflow.agent.runner import InvestigationRunner
from forgeflow.api.deps import IndustrialServiceDep, LLMProviderDep
from forgeflow.config import get_settings
from forgeflow.mcp.runtime import build_tool_gateway

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationResult)
async def create_investigation(
    body: InvestigationRequest,
    service: IndustrialServiceDep,
    llm: LLMProviderDep,
) -> InvestigationResult:
    settings = get_settings()
    gateway = build_tool_gateway(service, timeout_seconds=settings.mcp_tool_timeout_seconds)
    as_of = settings.investigation_as_of or datetime.now(UTC)
    runner = InvestigationRunner(tools=gateway, llm=llm, as_of=as_of)
    return await runner.run(body.request)
