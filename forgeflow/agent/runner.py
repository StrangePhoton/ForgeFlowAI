"""Run a single investigation through the compiled LangGraph workflow."""

from datetime import UTC, datetime
from typing import Any

from forgeflow.agent.graph.investigation import build_investigation_graph
from forgeflow.agent.models import (
    EvidenceBundle,
    InvestigationPlan,
    InvestigationReport,
    InvestigationResult,
)
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.state import InvestigationState
from forgeflow.mcp.runtime import McpToolGateway


class InvestigationRunner:
    def __init__(
        self,
        *,
        tools: McpToolGateway,
        llm: LLMProvider,
        as_of: datetime,
    ) -> None:
        self._graph = build_investigation_graph(tools=tools, llm=llm)
        self._as_of = as_of.astimezone(UTC) if as_of.tzinfo else as_of.replace(tzinfo=UTC)

    async def run(self, request: str) -> InvestigationResult:
        initial: InvestigationState = {
            "request": request,
            "as_of": self._as_of.isoformat(),
            "equipment_code": None,
            "analysis": None,
            "plan": None,
            "equipment": None,
            "telemetry": [],
            "alarms": [],
            "maintenance": [],
            "evidence": None,
            "report": None,
            "errors": [],
        }
        raw: dict[str, Any] = await self._graph.ainvoke(initial)
        plan = InvestigationPlan.model_validate(raw.get("plan") or {})
        evidence = EvidenceBundle.model_validate(raw.get("evidence") or {})
        report = InvestigationReport.model_validate(
            raw.get("report") or {"title": "Investigation", "summary": ""}
        )
        return InvestigationResult(
            request=request,
            equipment_code=raw.get("equipment_code"),
            plan=plan,
            evidence=evidence,
            report=report,
        )
