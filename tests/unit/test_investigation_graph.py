"""LangGraph investigation workflow with a mock LLM. No paid API."""

import pytest
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.mock import MockLLMProvider
from forgeflow.agent.runner import InvestigationRunner
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK, TEMP_HIGH_CODE
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.services.snapshot import InMemoryIndustrialReader


def _setup() -> tuple[InMemoryIndustrialReader, InvestigationRunner, ApprovalGate]:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gate = ApprovalGate()
    runner = InvestigationRunner(
        tools=build_tool_gateway(reader, authorizer=gate),
        llm=MockLLMProvider(),
        as_of=DEMO_CLOCK,
        approval_gate=gate,
    )
    return reader, runner, gate


@pytest.mark.asyncio
async def test_cnc_042_investigation_is_evidence_backed() -> None:
    _reader, runner, _gate = _setup()
    result = await runner.run("Investigate overheating on CNC-042")
    assert result.equipment_code == CNC_CODE
    assert result.plan.steps
    assert result.report.evidence_sufficient is True
    assert result.report.confidence == "high"
    assert result.report.likely_cause is not None
    kinds = {item.kind for item in result.report.findings}
    assert kinds >= {"FACT", "INFERENCE", "RECOMMENDATION"}
    statements = " ".join(item.statement for item in result.report.findings)
    assert TEMP_HIGH_CODE in statements
    assert "coolant" in statements.lower()
    assert "inspection" in statements.lower() or "overdue" in statements.lower()
    sources = {item.source for item in result.report.findings}
    assert "search_documentation" in sources
    assert "cnc-042-cooling.md" in statements
    assert result.status == "awaiting_approval"
    assert result.approval is not None
    assert result.work_order is None


@pytest.mark.asyncio
async def test_unknown_asset_investigation_is_insufficient() -> None:
    _reader, runner, _gate = _setup()
    result = await runner.run("Investigate vibration on PRESS-NOPE-99")
    assert result.report.evidence_sufficient is False
    assert result.report.confidence == "insufficient"
    assert result.status == "completed"
    assert result.work_order is None


@pytest.mark.asyncio
async def test_peer_asset_does_not_get_cnc_cause() -> None:
    _reader, runner, _gate = _setup()
    result = await runner.run("Investigate PUMP-AX200")
    assert result.equipment_code == "PUMP-AX200"
    assert result.report.evidence_sufficient is False
    assert result.report.likely_cause is None
    assert result.status == "completed"
    assert result.work_order is None
