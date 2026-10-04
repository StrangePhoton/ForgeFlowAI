"""Typed agent graph state."""

from typing import Any, TypedDict


class InvestigationState(TypedDict):
    request: str
    as_of: str
    investigation_id: str
    equipment_code: str | None
    analysis: dict[str, Any] | None
    plan: dict[str, Any] | None
    equipment: dict[str, Any] | None
    telemetry: list[dict[str, Any]]
    alarms: list[dict[str, Any]]
    maintenance: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    evidence: dict[str, Any] | None
    report: dict[str, Any] | None
    proposed_action: dict[str, Any] | None
    approval: dict[str, Any] | None
    work_order: dict[str, Any] | None
    run_status: str
    errors: list[str]
