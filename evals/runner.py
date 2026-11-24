"""Execute the synthetic investigation benchmark and write reports."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from forgeflow.agent.policies import ApprovalGate
from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.providers.factory import create_llm_provider
from forgeflow.agent.runner import InvestigationRunner
from forgeflow.config import get_settings
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.services.snapshot import InMemoryIndustrialReader

from evals.evaluators.score import aggregate, score_scenario
from evals.models import Dataset, EvalReport, Scenario, ScenarioScore

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = PACKAGE_DIR / "datasets" / "scenarios.json"
DEFAULT_REPORTS = PACKAGE_DIR / "reports"


def load_dataset(path: Path) -> Dataset:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return Dataset.model_validate(payload)


async def run_benchmark(dataset: Dataset, *, dataset_path: str) -> EvalReport:
    settings = get_settings()
    llm = create_llm_provider(settings)
    scores: list[ScenarioScore] = []
    for scenario in dataset.scenarios:
        scores.append(await _run_scenario(scenario, llm))
    return EvalReport(
        generated_at=datetime.now(UTC),
        llm_provider=settings.llm_provider,
        as_of=DEMO_CLOCK,
        dataset=dataset_path,
        scenario_count=len(scores),
        metrics=aggregate(scores),
        scenarios=scores,
    )


def write_reports(report: EvalReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "latest.json"
    md_path = output_dir / "latest.md"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ForgeFlow synthetic evaluations")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument(
        "--provider",
        default="mock",
        help="LLM provider for this run. Default mock so the command needs no model server.",
    )
    args = parser.parse_args(argv)
    os.environ["LLM_PROVIDER"] = args.provider
    get_settings.cache_clear()
    dataset = load_dataset(args.dataset)
    report = asyncio.run(run_benchmark(dataset, dataset_path=str(args.dataset)))
    json_path, md_path = write_reports(report, args.output_dir)
    print(json_path)
    print(md_path)
    print(f"task_completion_rate={report.metrics.task_completion_rate:.3f}")
    return 0


async def _run_scenario(scenario: Scenario, llm: LLMProvider) -> ScenarioScore:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gate = ApprovalGate()
    tools = build_tool_gateway(reader, authorizer=gate)
    runner = InvestigationRunner(
        tools=tools,
        llm=llm,
        as_of=DEMO_CLOCK,
        approval_gate=gate,
    )
    started = perf_counter()
    result = await runner.run(scenario.request)
    latency_ms = (perf_counter() - started) * 1000
    first_invocations = list(tools.invocations)
    after = None
    if scenario.approve_after and result.investigation_id and result.status == "awaiting_approval":
        approve_started = perf_counter()
        after = await runner.resume(result.investigation_id, {"decision": "approve"})
        latency_ms += (perf_counter() - approve_started) * 1000
    return score_scenario(
        scenario,
        result,
        first_invocations,
        latency_ms=latency_ms,
        after=after,
    )


def _render_markdown(report: EvalReport) -> str:
    metrics = report.metrics
    lines = [
        "# ForgeFlow evaluation report",
        "",
        f"Generated at: {report.generated_at.isoformat()}",
        f"LLM provider: {report.llm_provider}",
        f"Investigation clock: {report.as_of.isoformat()}",
        f"Dataset: `{report.dataset}`",
        f"Scenarios: {report.scenario_count}",
        "",
        "These numbers were produced by `python -m evals`. They are not hand-written.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| task_completion_rate | {metrics.task_completion_rate:.3f} |",
        f"| structured_output_validity | {metrics.structured_output_validity:.3f} |",
        f"| required_tool_recall | {metrics.required_tool_recall:.3f} |",
        f"| tool_selection_accuracy | {metrics.tool_selection_accuracy:.3f} |",
        f"| forbidden_tool_invocation_rate | {metrics.forbidden_tool_invocation_rate:.3f} |",
        f"| retrieval_precision | {_fmt(metrics.retrieval_precision)} |",
        f"| approval_policy_compliance_rate | {metrics.approval_policy_compliance_rate:.3f} |",
        f"| unsupported_claim_rate | {metrics.unsupported_claim_rate:.3f} |",
        f"| mean_latency_ms | {metrics.mean_latency_ms:.1f} |",
        f"| token_usage | {_fmt_int(metrics.token_usage)} |",
        "",
        "## Scenarios",
        "",
        "| ID | Completed | Status | Recall | Forbidden | Latency ms |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report.scenarios:
        lines.append(
            f"| {item.id} | {item.task_completed} | {item.status} | "
            f"{item.required_tool_recall:.2f} | {item.forbidden_tool_invocations} | "
            f"{item.latency_ms:.1f} |"
        )
        if item.notes:
            lines.append("")
            lines.append(f"- `{item.id}` notes: {'; '.join(item.notes)}")
    lines.append("")
    return "\n".join(lines)


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)
