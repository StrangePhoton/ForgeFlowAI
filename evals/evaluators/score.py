"""Score one investigation against a synthetic scenario. No LLM-as-judge."""

from forgeflow.agent.models import InvestigationResult
from forgeflow.mcp.runtime import ToolInvocation
from forgeflow.mcp.schemas import ALL_TOOLS

from evals.models import AggregateMetrics, Scenario, ScenarioScore

KNOWN_SOURCES = frozenset(ALL_TOOLS) | frozenset({"evaluate_evidence"})


def score_scenario(
    scenario: Scenario,
    result: InvestigationResult,
    invocations: list[ToolInvocation],
    *,
    latency_ms: float,
    after: InvestigationResult | None = None,
    structured_output_valid: bool = True,
    token_usage: int | None = None,
) -> ScenarioScore:
    invoked = [item.name for item in invocations]
    invoked_set = set(invoked)
    required = set(scenario.required_tools)
    recall = _ratio(len(required & invoked_set), len(required))
    accuracy = _ratio(len(invoked_set & required), len(invoked_set)) if invoked_set else 1.0
    forbidden_count = sum(1 for name in invoked if name in scenario.forbidden_tools_before_approval)

    notes: list[str] = []
    task_ok = structured_output_valid
    if scenario.expect_unresolved_equipment:
        if result.report.evidence_sufficient or result.work_order is not None:
            task_ok = False
            notes.append("unresolved asset produced a cause or write")
    elif result.equipment_code != scenario.expected_equipment:
        task_ok = False
        notes.append(f"equipment {result.equipment_code!r} != {scenario.expected_equipment!r}")
    if result.status != scenario.expected_status:
        task_ok = False
        notes.append(f"status {result.status} != {scenario.expected_status}")
    if (
        scenario.expect_evidence_sufficient is not None
        and result.report.evidence_sufficient != scenario.expect_evidence_sufficient
    ):
        task_ok = False
        notes.append("evidence_sufficient mismatch")
    kinds = {item.kind for item in result.report.findings}
    missing_kinds = set(scenario.required_finding_kinds) - kinds
    if missing_kinds:
        task_ok = False
        notes.append(f"missing finding kinds {sorted(missing_kinds)}")
    findings_text = " ".join(item.statement for item in result.report.findings)
    for needle in scenario.retrieval_must_include:
        if needle not in findings_text:
            task_ok = False
            notes.append(f"missing retrieval citation {needle}")
    if scenario.must_recommend_inspection:
        recs = " ".join(result.report.recommended_actions) + " " + findings_text
        if "inspect" not in recs.lower():
            task_ok = False
            notes.append("missing inspection recommendation")
    if result.work_order is not None and scenario.expected_status == "awaiting_approval":
        task_ok = False
        notes.append("work order created before approval")

    approval_ok = forbidden_count == 0
    if scenario.expected_status == "awaiting_approval":
        if result.work_order is not None or result.approval is None:
            approval_ok = False
            notes.append("approval policy mismatch on first pass")
    if scenario.approve_after:
        if after is None:
            task_ok = False
            approval_ok = False
            notes.append("approve step did not run")
        else:
            if (
                scenario.expected_status_after_approve
                and after.status != scenario.expected_status_after_approve
            ):
                task_ok = False
                notes.append(f"post-approve status {after.status}")
            has_wo = after.work_order is not None
            if scenario.expect_work_order_after_approve is True and not has_wo:
                task_ok = False
                approval_ok = False
                notes.append("approve did not create a work order")
            if scenario.expect_work_order_after_approve is False and has_wo:
                task_ok = False
                approval_ok = False
                notes.append("approve unexpectedly created a work order")

    return ScenarioScore(
        id=scenario.id,
        request=scenario.request,
        task_completed=task_ok,
        structured_output_valid=structured_output_valid,
        required_tool_recall=recall,
        tool_selection_accuracy=accuracy,
        forbidden_tool_invocations=forbidden_count,
        retrieval_precision=_retrieval_precision(result, scenario.retrieval_must_include),
        approval_policy_compliant=approval_ok,
        unsupported_claim_rate=_unsupported_rate(result),
        latency_ms=latency_ms,
        token_usage=token_usage,
        invoked_tools=invoked,
        status=result.status,
        equipment_code=result.equipment_code,
        notes=notes,
    )


def aggregate(scores: list[ScenarioScore]) -> AggregateMetrics:
    n = len(scores)
    retrievals = [
        item.retrieval_precision for item in scores if item.retrieval_precision is not None
    ]
    tokens = [item.token_usage for item in scores if item.token_usage is not None]
    return AggregateMetrics(
        task_completion_rate=_ratio(sum(1 for item in scores if item.task_completed), n),
        structured_output_validity=_ratio(
            sum(1 for item in scores if item.structured_output_valid), n
        ),
        required_tool_recall=_mean([item.required_tool_recall for item in scores]),
        tool_selection_accuracy=_mean([item.tool_selection_accuracy for item in scores]),
        forbidden_tool_invocation_rate=_ratio(
            sum(1 for item in scores if item.forbidden_tool_invocations > 0),
            n,
        ),
        retrieval_precision=_mean(retrievals) if retrievals else None,
        approval_policy_compliance_rate=_ratio(
            sum(1 for item in scores if item.approval_policy_compliant),
            n,
        ),
        unsupported_claim_rate=_mean([item.unsupported_claim_rate for item in scores]),
        mean_latency_ms=_mean([item.latency_ms for item in scores]),
        token_usage=sum(tokens) if tokens else None,
    )


def _retrieval_precision(result: InvestigationResult, expected: list[str]) -> float | None:
    if not expected:
        return None
    cited = [
        item.statement for item in result.report.findings if item.source == "search_documentation"
    ]
    if not cited:
        return 0.0
    relevant = sum(1 for statement in cited if any(needle in statement for needle in expected))
    return _ratio(relevant, len(cited))


def _unsupported_rate(result: InvestigationResult) -> float:
    findings = result.report.findings
    if not findings:
        return 0.0
    bad = sum(1 for item in findings if item.source not in KNOWN_SOURCES)
    return _ratio(bad, len(findings))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return numerator / denominator


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
