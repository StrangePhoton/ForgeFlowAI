"""Protected write policy. The LLM cannot authorize create_work_order."""

import pytest
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.mock import MockLLMProvider
from forgeflow.agent.runner import InvestigationRunner
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.errors import ToolAuthorizationError
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.mcp.schemas import CREATE_WORK_ORDER
from forgeflow.services.snapshot import InMemoryIndustrialReader


def _args(key: str = "investigation:test:create_work_order") -> dict[str, str]:
    return {
        "equipment_id": CNC_CODE,
        "title": "Inspect coolant loop and restore flow",
        "description": "Protected write",
        "priority": "high",
        "idempotency_key": key,
    }


@pytest.mark.asyncio
async def test_create_work_order_denied_without_approval() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(reader, authorizer=ApprovalGate())
    with pytest.raises(ToolAuthorizationError):
        await gateway.call(CREATE_WORK_ORDER, _args())
    assert reader._created_work_orders == []


@pytest.mark.asyncio
async def test_approve_then_resume_creates_exactly_one_work_order() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gate = ApprovalGate()
    runner = InvestigationRunner(
        tools=build_tool_gateway(reader, authorizer=gate),
        llm=MockLLMProvider(),
        as_of=DEMO_CLOCK,
        approval_gate=gate,
    )
    started = await runner.run("Investigate overheating on CNC-042")
    assert started.status == "awaiting_approval"
    assert started.investigation_id is not None
    assert started.work_order is None
    finished = await runner.resume(
        started.investigation_id,
        {"decision": "approve"},
    )
    assert finished.status == "completed"
    assert finished.work_order is not None
    assert len(reader._created_work_orders) == 1
    replay = await reader.create_work_order(
        equipment_id=CNC_CODE,
        title=finished.work_order.title,
        description=finished.work_order.description,
        priority=finished.work_order.priority,
        idempotency_key=finished.work_order.idempotency_key or "missing",
        source_investigation_id=started.investigation_id,
    )
    assert replay.id == finished.work_order.id
    assert len(reader._created_work_orders) == 1


@pytest.mark.asyncio
async def test_reject_resume_creates_no_work_order() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gate = ApprovalGate()
    runner = InvestigationRunner(
        tools=build_tool_gateway(reader, authorizer=gate),
        llm=MockLLMProvider(),
        as_of=DEMO_CLOCK,
        approval_gate=gate,
    )
    started = await runner.run("Investigate overheating on CNC-042")
    finished = await runner.resume(
        started.investigation_id or "",
        {"decision": "reject", "reason": "Not this shift"},
    )
    assert finished.status == "rejected"
    assert finished.work_order is None
    assert reader._created_work_orders == []
