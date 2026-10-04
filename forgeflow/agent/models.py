"""Structured agent outputs. Critical model results are Pydantic models, not free text."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from forgeflow.domain.schemas import WorkOrderOut

EvidenceKind = Literal["FACT", "INFERENCE", "RECOMMENDATION"]
Confidence = Literal["high", "medium", "low", "insufficient"]


class RequestAnalysis(BaseModel):
    equipment_code: str | None = None
    intent: str = "investigate"
    summary: str = ""


class InvestigationPlan(BaseModel):
    steps: list[str] = Field(default_factory=list)
    lookback_days: int = Field(default=30, ge=1, le=365)
    rationale: str = ""


class EvidenceItem(BaseModel):
    kind: EvidenceKind
    statement: str
    source: str


class EvidenceBundle(BaseModel):
    reading_count: int = 0
    alarm_count: int = 0
    temp_high_count: int = 0
    baseline_mean_temperature: float | None = None
    recent_mean_temperature: float | None = None
    baseline_mean_coolant_flow: float | None = None
    recent_mean_coolant_flow: float | None = None
    overdue_maintenance: list[str] = Field(default_factory=list)
    facts: list[EvidenceItem] = Field(default_factory=list)
    inferences: list[EvidenceItem] = Field(default_factory=list)
    recommendations: list[EvidenceItem] = Field(default_factory=list)
    evidence_sufficient: bool = False
    likely_cause: str | None = None
    confidence: Confidence = "insufficient"


class InvestigationReport(BaseModel):
    title: str
    equipment_code: str | None = None
    summary: str
    findings: list[EvidenceItem] = Field(default_factory=list)
    likely_cause: str | None = None
    confidence: Confidence = "insufficient"
    evidence_sufficient: bool = False
    recommended_actions: list[str] = Field(default_factory=list)


class InvestigationRequest(BaseModel):
    request: str = Field(min_length=1, max_length=4000)


class PendingApproval(BaseModel):
    investigation_id: str
    tool_name: str
    risk: str
    proposal: dict[str, Any]


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None


class InvestigationResult(BaseModel):
    request: str
    equipment_code: str | None
    plan: InvestigationPlan
    evidence: EvidenceBundle
    report: InvestigationReport
    status: Literal["completed", "awaiting_approval", "rejected"] = "completed"
    investigation_id: str | None = None
    approval: PendingApproval | None = None
    work_order: WorkOrderOut | None = None
