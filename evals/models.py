"""Dataset and report schemas. Numbers in reports come only from runner output."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

InvestigationStatus = Literal["completed", "awaiting_approval", "rejected"]


class Scenario(BaseModel):
    id: str
    request: str
    expected_equipment: str | None = None
    expect_unresolved_equipment: bool = False
    required_tools: list[str] = Field(default_factory=list)
    forbidden_tools_before_approval: list[str] = Field(default_factory=list)
    expected_status: InvestigationStatus
    expect_evidence_sufficient: bool | None = None
    required_finding_kinds: list[str] = Field(default_factory=list)
    retrieval_must_include: list[str] = Field(default_factory=list)
    must_recommend_inspection: bool = False
    approve_after: bool = False
    expected_status_after_approve: InvestigationStatus | None = None
    expect_work_order_after_approve: bool | None = None


class Dataset(BaseModel):
    version: int = 1
    scenarios: list[Scenario]


class ScenarioScore(BaseModel):
    id: str
    request: str
    task_completed: bool
    structured_output_valid: bool
    required_tool_recall: float
    tool_selection_accuracy: float
    forbidden_tool_invocations: int
    retrieval_precision: float | None
    approval_policy_compliant: bool
    unsupported_claim_rate: float
    latency_ms: float
    token_usage: int | None
    invoked_tools: list[str]
    status: str
    equipment_code: str | None
    notes: list[str] = Field(default_factory=list)


class AggregateMetrics(BaseModel):
    task_completion_rate: float
    structured_output_validity: float
    required_tool_recall: float
    tool_selection_accuracy: float
    forbidden_tool_invocation_rate: float
    retrieval_precision: float | None
    approval_policy_compliance_rate: float
    unsupported_claim_rate: float
    mean_latency_ms: float
    token_usage: int | None


class EvalReport(BaseModel):
    generated_at: datetime
    llm_provider: str
    as_of: datetime
    dataset: str
    scenario_count: int
    metrics: AggregateMetrics
    scenarios: list[ScenarioScore]
