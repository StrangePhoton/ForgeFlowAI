"""Deterministic in-process LLM used by the default test suite."""

import re

from pydantic import BaseModel

from forgeflow.agent.models import (
    InvestigationPlan,
    InvestigationReport,
    RequestAnalysis,
)
from forgeflow.errors import StructuredOutputError

_EQUIPMENT_CODE = re.compile(r"\b([A-Z]{2,}(?:-[A-Z0-9]+)+)\b", re.IGNORECASE)

DEFAULT_STEPS = [
    "resolve_equipment",
    "retrieve_telemetry",
    "retrieve_alarms",
    "retrieve_maintenance",
    "evaluate_evidence",
    "generate_report",
]


class MockLLMProvider:
    """Never calls a network API. Returns schema-valid objects for investigations."""

    async def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        temperature: float | None = None,
    ) -> BaseModel:
        del system, temperature
        if schema is RequestAnalysis:
            match = _EQUIPMENT_CODE.search(user)
            code = match.group(1).upper() if match else None
            return RequestAnalysis(
                equipment_code=code,
                intent="investigate",
                summary=user.strip()[:500],
            )
        if schema is InvestigationPlan:
            return InvestigationPlan(
                steps=list(DEFAULT_STEPS),
                lookback_days=30,
                rationale="Gather equipment identity, telemetry, alarms, and maintenance history.",
            )
        if schema is InvestigationReport:
            code_match = _EQUIPMENT_CODE.search(user)
            code = code_match.group(1).upper() if code_match else None
            return InvestigationReport(
                title=f"Investigation report for {code or 'unknown equipment'}",
                equipment_code=code,
                summary="Mock provider summary. Deterministic evidence is attached by the graph.",
                findings=[],
                likely_cause=None,
                confidence="insufficient",
                evidence_sufficient=False,
                recommended_actions=[],
            )
        raise StructuredOutputError(f"Mock LLM has no fixture for {schema.__name__}")
