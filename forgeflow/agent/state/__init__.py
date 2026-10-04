"""Typed agent graph state."""

from typing import Any, TypedDict


class InvestigationState(TypedDict):
    request: str
    as_of: str
    equipment_code: str | None
    analysis: dict[str, Any] | None
    plan: dict[str, Any] | None
    equipment: dict[str, Any] | None
    telemetry: list[dict[str, Any]]
    alarms: list[dict[str, Any]]
    maintenance: list[dict[str, Any]]
    evidence: dict[str, Any] | None
    report: dict[str, Any] | None
    errors: list[str]
