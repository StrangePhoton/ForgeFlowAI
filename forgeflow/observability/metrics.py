"""Helpers that record OpenTelemetry instruments. No-ops until telemetry is configured."""

from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram

_DURATION_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
)

_http_requests: Counter | None = None
_http_duration: Histogram | None = None
_agent_runs: Counter | None = None
_agent_duration: Histogram | None = None
_tool_calls: Counter | None = None
_tool_duration: Histogram | None = None
_llm_requests: Counter | None = None
_llm_duration: Histogram | None = None
_llm_tokens: Counter | None = None
_retrieval_requests: Counter | None = None
_retrieval_duration: Histogram | None = None
_approvals: Counter | None = None


def init_instruments() -> None:
    meter = metrics.get_meter("forgeflow")
    global _http_requests, _http_duration, _agent_runs, _agent_duration
    global _tool_calls, _tool_duration, _llm_requests, _llm_duration, _llm_tokens
    global _retrieval_requests, _retrieval_duration, _approvals
    _http_requests = meter.create_counter("forgeflow.http.requests", unit="1")
    _http_duration = meter.create_histogram(
        "forgeflow.http.duration",
        unit="s",
        explicit_bucket_boundaries_advisory=_DURATION_BUCKETS,
    )
    _agent_runs = meter.create_counter("forgeflow.agent.runs", unit="1")
    _agent_duration = meter.create_histogram(
        "forgeflow.agent.duration",
        unit="s",
        explicit_bucket_boundaries_advisory=_DURATION_BUCKETS,
    )
    _tool_calls = meter.create_counter("forgeflow.tool.calls", unit="1")
    _tool_duration = meter.create_histogram(
        "forgeflow.tool.duration",
        unit="s",
        explicit_bucket_boundaries_advisory=_DURATION_BUCKETS,
    )
    _llm_requests = meter.create_counter("forgeflow.llm.requests", unit="1")
    _llm_duration = meter.create_histogram(
        "forgeflow.llm.duration",
        unit="s",
        explicit_bucket_boundaries_advisory=_DURATION_BUCKETS,
    )
    _llm_tokens = meter.create_counter("forgeflow.llm.tokens", unit="1")
    _retrieval_requests = meter.create_counter("forgeflow.retrieval.requests", unit="1")
    _retrieval_duration = meter.create_histogram(
        "forgeflow.retrieval.duration",
        unit="s",
        explicit_bucket_boundaries_advisory=_DURATION_BUCKETS,
    )
    _approvals = meter.create_counter("forgeflow.approvals", unit="1")


def record_http_request(method: str, route: str, status: str, duration_s: float) -> None:
    if _http_requests is None or _http_duration is None:
        return
    labels = {"http.method": method, "http.route": route, "http.status_code": status}
    _http_requests.add(1, labels)
    _http_duration.record(duration_s, labels)


def record_agent_run(outcome: str, duration_s: float) -> None:
    if _agent_runs is None or _agent_duration is None:
        return
    labels = {"outcome": outcome}
    _agent_runs.add(1, labels)
    _agent_duration.record(duration_s, labels)


def record_tool_call(tool: str, ok: bool, duration_s: float) -> None:
    if _tool_calls is None or _tool_duration is None:
        return
    labels = {"tool": tool, "ok": str(ok).lower()}
    _tool_calls.add(1, labels)
    _tool_duration.record(duration_s, labels)


def record_llm_call(provider: str, ok: bool, duration_s: float) -> None:
    if _llm_requests is None or _llm_duration is None:
        return
    labels = {"provider": provider, "ok": str(ok).lower()}
    _llm_requests.add(1, labels)
    _llm_duration.record(duration_s, labels)


def record_llm_tokens(provider: str, prompt_tokens: int, completion_tokens: int) -> None:
    if _llm_tokens is None:
        return
    if prompt_tokens:
        _llm_tokens.add(prompt_tokens, {"provider": provider, "type": "prompt"})
    if completion_tokens:
        _llm_tokens.add(completion_tokens, {"provider": provider, "type": "completion"})


def record_retrieval(ok: bool, duration_s: float) -> None:
    if _retrieval_requests is None or _retrieval_duration is None:
        return
    labels = {"ok": str(ok).lower()}
    _retrieval_requests.add(1, labels)
    _retrieval_duration.record(duration_s, labels)


def record_approval_request() -> None:
    if _approvals is None:
        return
    _approvals.add(1)
