"""Run a single investigation through the compiled LangGraph workflow."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from forgeflow.agent.graph.investigation import build_investigation_graph
from forgeflow.agent.models import (
    EvidenceBundle,
    InvestigationPlan,
    InvestigationReport,
    InvestigationResult,
    PendingApproval,
)
from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.state import InvestigationState
from forgeflow.domain.schemas import WorkOrderOut
from forgeflow.errors import NotFoundError
from forgeflow.mcp.runtime import McpToolGateway


class InvestigationRunner:
    def __init__(
        self,
        *,
        tools: McpToolGateway,
        llm: LLMProvider,
        as_of: datetime,
        checkpointer: Any | None = None,
        approval_gate: ApprovalGate | None = None,
    ) -> None:
        self._checkpointer = checkpointer or MemorySaver()
        self._gate = approval_gate or ApprovalGate()
        self._graph = build_investigation_graph(
            tools=tools,
            llm=llm,
            approval_gate=self._gate,
            checkpointer=self._checkpointer,
        )
        self._as_of = as_of.astimezone(UTC) if as_of.tzinfo else as_of.replace(tzinfo=UTC)

    async def run(
        self, request: str, *, investigation_id: str | None = None
    ) -> InvestigationResult:
        thread_id = investigation_id or str(uuid4())
        initial: InvestigationState = {
            "request": request,
            "as_of": self._as_of.isoformat(),
            "investigation_id": thread_id,
            "equipment_code": None,
            "analysis": None,
            "plan": None,
            "equipment": None,
            "telemetry": [],
            "alarms": [],
            "maintenance": [],
            "documents": [],
            "evidence": None,
            "report": None,
            "proposed_action": None,
            "approval": None,
            "work_order": None,
            "run_status": "running",
            "errors": [],
        }
        config = {"configurable": {"thread_id": thread_id}}
        raw = await self._invoke(initial, config)
        return await self._to_result(raw, thread_id, request)

    async def resume(self, investigation_id: str, decision: dict[str, Any]) -> InvestigationResult:
        config = {"configurable": {"thread_id": investigation_id}}
        snapshot = await self._graph.aget_state(config)
        if snapshot.values is None or snapshot.values == {}:
            raise NotFoundError(f"Investigation {investigation_id} was not found")
        raw = await self._invoke(Command(resume=decision), config)
        values = dict(snapshot.values)
        request = str(raw.get("request") or values.get("request") or "")
        return await self._to_result(raw, investigation_id, request)

    async def _invoke(self, payload: Any, config: dict[str, Any]) -> dict[str, Any]:
        try:
            raw = await self._graph.ainvoke(payload, config)
        except GraphInterrupt:
            snapshot = await self._graph.aget_state(config)
            return dict(snapshot.values or {})
        return dict(raw or {})

    async def _to_result(
        self,
        raw: dict[str, Any],
        thread_id: str,
        request: str,
    ) -> InvestigationResult:
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await self._graph.aget_state(config)
        values = dict(snapshot.values or raw)
        pending = _interrupt_payload(snapshot) or _interrupt_from_values(raw)
        status = str(values.get("run_status") or "completed")
        approval_view: PendingApproval | None = None
        if pending is not None:
            status = "awaiting_approval"
            raw_proposal = pending.get("proposal")
            proposal = raw_proposal if isinstance(raw_proposal, dict) else {}
            approval_view = PendingApproval(
                investigation_id=thread_id,
                tool_name=str(proposal.get("tool") or "create_work_order"),
                risk=str(pending.get("risk") or "high"),
                proposal=proposal,
            )
        if status not in {"completed", "awaiting_approval", "rejected"}:
            status = "awaiting_approval" if pending is not None else "completed"
        work_order = None
        if values.get("work_order"):
            work_order = WorkOrderOut.model_validate(values["work_order"])
        plan = InvestigationPlan.model_validate(values.get("plan") or {})
        evidence = EvidenceBundle.model_validate(values.get("evidence") or {})
        report = InvestigationReport.model_validate(
            values.get("report") or {"title": "Investigation", "summary": ""}
        )
        return InvestigationResult(
            request=request,
            equipment_code=values.get("equipment_code"),
            plan=plan,
            evidence=evidence,
            report=report,
            status=status,  # type: ignore[arg-type]
            investigation_id=thread_id,
            approval=approval_view,
            work_order=work_order,
        )


def _interrupt_from_values(raw: dict[str, Any]) -> dict[str, Any] | None:
    interrupts = raw.get("__interrupt__")
    if isinstance(interrupts, (list, tuple)):
        for item in interrupts:
            value = getattr(item, "value", item)
            if isinstance(value, dict):
                return value
    return None


def _interrupt_payload(snapshot: Any) -> dict[str, Any] | None:
    tasks = getattr(snapshot, "tasks", ()) or ()
    for task in tasks:
        interrupts = getattr(task, "interrupts", ()) or ()
        for item in interrupts:
            value = getattr(item, "value", item)
            if isinstance(value, dict):
                return value
    return None
