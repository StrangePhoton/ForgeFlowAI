"""Synthetic evaluation harness. Uses the in-process mock LLM only."""

from pathlib import Path

from evals.models import Dataset
from evals.runner import DEFAULT_DATASET, load_dataset, run_benchmark, write_reports
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.mcp.schemas import GET_EQUIPMENT
from forgeflow.services.snapshot import InMemoryIndustrialReader


def test_default_dataset_loads() -> None:
    dataset = load_dataset(DEFAULT_DATASET)
    assert isinstance(dataset, Dataset)
    ids = {item.id for item in dataset.scenarios}
    assert "cnc-042-overheating" in ids
    assert "prompt-injection-no-skip-approval" in ids


async def test_gateway_records_invocations() -> None:
    tools = build_tool_gateway(InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK)))
    await tools.call(GET_EQUIPMENT, {"equipment_id": CNC_CODE})
    assert tools.invocations[0].name == GET_EQUIPMENT
    assert tools.invocations[0].ok is True


async def test_benchmark_completes_cnc_and_writes_reports(tmp_path: Path) -> None:
    dataset = load_dataset(DEFAULT_DATASET)
    report = await run_benchmark(dataset, dataset_path=str(DEFAULT_DATASET))
    by_id = {item.id: item for item in report.scenarios}
    cnc = by_id["cnc-042-overheating"]
    assert cnc.task_completed is True
    assert cnc.status == "awaiting_approval"
    assert cnc.required_tool_recall == 1.0
    assert cnc.forbidden_tool_invocations == 0
    assert cnc.approval_policy_compliant is True
    assert cnc.retrieval_precision is not None
    assert cnc.retrieval_precision > 0
    assert by_id["unknown-asset"].task_completed is True
    assert by_id["pump-ax200-no-false-cause"].task_completed is True
    assert by_id["prompt-injection-no-skip-approval"].status == "awaiting_approval"
    assert by_id["prompt-injection-no-skip-approval"].forbidden_tool_invocations == 0
    assert report.metrics.task_completion_rate == 1.0
    json_path, md_path = write_reports(report, tmp_path)
    assert json_path.is_file()
    assert md_path.is_file()
    body = json_path.read_text(encoding="utf-8")
    assert "task_completion_rate" in body
    assert "cnc-042-overheating" in md_path.read_text(encoding="utf-8")
