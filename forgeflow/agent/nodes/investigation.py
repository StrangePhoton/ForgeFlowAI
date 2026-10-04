"""Investigation graph nodes. Tool execution goes through MCP; facts are deterministic."""

from datetime import datetime, timedelta
from typing import Any, TypeVar

from pydantic import BaseModel

from forgeflow.agent.evidence import evaluate_evidence, report_actions
from forgeflow.agent.models import (
    EvidenceBundle,
    InvestigationPlan,
    InvestigationReport,
    RequestAnalysis,
)
from forgeflow.agent.parsing import extract_equipment_code
from forgeflow.agent.prompts import ANALYZE_SYSTEM, PLAN_SYSTEM, REPORT_SYSTEM
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.providers.mock import DEFAULT_STEPS
from forgeflow.agent.state import InvestigationState
from forgeflow.errors import ForgeFlowError, ProviderError, StructuredOutputError
from forgeflow.mcp.runtime import McpToolGateway
from forgeflow.mcp.schemas import (
    GET_ALARM_HISTORY,
    GET_EQUIPMENT,
    GET_MAINTENANCE_HISTORY,
    GET_SENSOR_HISTORY,
)

TModel = TypeVar("TModel", bound=BaseModel)


class InvestigationNodes:
    def __init__(self, *, tools: McpToolGateway, llm: LLMProvider) -> None:
        self._tools = tools
        self._llm = llm

    async def analyze_request(self, state: InvestigationState) -> dict[str, Any]:
        analysis = await self._structured(
            schema=RequestAnalysis,
            system=ANALYZE_SYSTEM,
            user=state["request"],
            fallback=RequestAnalysis(
                equipment_code=extract_equipment_code(state["request"]),
                intent="investigate",
                summary=state["request"].strip()[:500],
            ),
        )
        code = analysis.equipment_code or extract_equipment_code(state["request"])
        if code:
            analysis = analysis.model_copy(update={"equipment_code": code})
        return {"analysis": analysis.model_dump(), "equipment_code": analysis.equipment_code}

    async def create_plan(self, state: InvestigationState) -> dict[str, Any]:
        user = (
            f"Request: {state['request']}\n"
            f"Equipment: {state.get('equipment_code') or 'unknown'}\n"
            "Plan tool-backed steps only."
        )
        plan = await self._structured(
            schema=InvestigationPlan,
            system=PLAN_SYSTEM,
            user=user,
            fallback=InvestigationPlan(
                steps=list(DEFAULT_STEPS),
                lookback_days=30,
                rationale=(
                    "Look up the asset, then retrieve telemetry, alarms, and maintenance history."
                ),
            ),
        )
        if not plan.steps:
            plan = plan.model_copy(update={"steps": list(DEFAULT_STEPS)})
        return {"plan": plan.model_dump()}

    async def resolve_equipment(self, state: InvestigationState) -> dict[str, Any]:
        code = state.get("equipment_code")
        if not code:
            return {
                "equipment": None,
                "errors": ["No equipment identifier could be extracted from the request."],
            }
        try:
            item = await self._tools.call(GET_EQUIPMENT, {"equipment_id": code})
        except ForgeFlowError as exc:
            if exc.code == "not_found":
                return {"equipment": None, "errors": [exc.message]}
            raise
        return {"equipment": item, "equipment_code": str(item.get("code") or code)}

    async def retrieve_telemetry(self, state: InvestigationState) -> dict[str, Any]:
        return {"telemetry": await self._history(state, GET_SENSOR_HISTORY)}

    async def retrieve_alarms(self, state: InvestigationState) -> dict[str, Any]:
        return {"alarms": await self._history(state, GET_ALARM_HISTORY)}

    async def retrieve_maintenance(self, state: InvestigationState) -> dict[str, Any]:
        code = state.get("equipment_code")
        if not code or state.get("equipment") is None:
            return {"maintenance": []}
        result = await self._tools.call(GET_MAINTENANCE_HISTORY, {"equipment_id": code})
        items = result.get("items")
        return {"maintenance": items if isinstance(items, list) else []}

    async def evaluate_evidence_node(self, state: InvestigationState) -> dict[str, Any]:
        as_of = datetime.fromisoformat(state["as_of"])
        bundle = evaluate_evidence(
            equipment_code=state.get("equipment_code"),
            equipment=state.get("equipment"),
            telemetry=state.get("telemetry") or [],
            alarms=state.get("alarms") or [],
            maintenance=state.get("maintenance") or [],
            as_of=as_of,
        )
        return {"evidence": bundle.model_dump(mode="json")}

    async def generate_report(self, state: InvestigationState) -> dict[str, Any]:
        evidence = state.get("evidence") or {}
        code = state.get("equipment_code")
        bundle = EvidenceBundle.model_validate(evidence)
        findings = list(bundle.facts) + list(bundle.inferences) + list(bundle.recommendations)
        deterministic = InvestigationReport(
            title=f"Investigation report for {code or 'unknown equipment'}",
            equipment_code=code,
            summary=_summary_from_evidence(code, evidence),
            findings=findings,
            likely_cause=bundle.likely_cause,
            confidence=bundle.confidence,
            evidence_sufficient=bundle.evidence_sufficient,
            recommended_actions=report_actions(bundle),
        )
        llm_report = await self._structured(
            schema=InvestigationReport,
            system=REPORT_SYSTEM,
            user=(
                f"Request: {state['request']}\n"
                f"Evidence JSON: {evidence}\n"
                "Return a title and summary. Do not invent facts."
            ),
            fallback=deterministic,
        )
        report = deterministic.model_copy(
            update={
                "title": llm_report.title,
                "summary": llm_report.summary or deterministic.summary,
            }
        )
        return {"report": report.model_dump(mode="json")}

    async def _history(self, state: InvestigationState, tool_name: str) -> list[dict[str, Any]]:
        code = state.get("equipment_code")
        if not code or state.get("equipment") is None:
            return []
        as_of = datetime.fromisoformat(state["as_of"])
        lookback = 30
        plan = state.get("plan") or {}
        raw_lookback = plan.get("lookback_days")
        if isinstance(raw_lookback, int) and raw_lookback > 0:
            lookback = raw_lookback
        start = as_of - timedelta(days=lookback)
        result = await self._tools.call(
            tool_name,
            {
                "equipment_id": code,
                "start": start.isoformat(),
                "end": as_of.isoformat(),
            },
        )
        items = result.get("items")
        return items if isinstance(items, list) else []

    async def _structured(
        self,
        *,
        schema: type[TModel],
        system: str,
        user: str,
        fallback: TModel,
    ) -> TModel:
        try:
            parsed = await self._llm.complete_structured(system=system, user=user, schema=schema)
        except (ProviderError, StructuredOutputError, ForgeFlowError):
            return fallback
        try:
            return schema.model_validate(parsed.model_dump())
        except Exception:
            return fallback


def _summary_from_evidence(code: str | None, evidence: dict[str, Any]) -> str:
    if not evidence.get("evidence_sufficient"):
        target = code or "the requested asset"
        return f"Insufficient evidence to name a confident root cause for {target}."
    cause = evidence.get("likely_cause") or "an operational anomaly"
    return f"Evidence supports a working cause for {code}: {cause}"


def route_after_equipment(state: InvestigationState) -> str:
    if state.get("equipment") is None:
        return "evaluate_evidence"
    return "retrieve_telemetry"
