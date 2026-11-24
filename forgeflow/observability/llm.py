"""LLM provider wrapper that records latency on every structured completion."""

from time import perf_counter

from pydantic import BaseModel

from forgeflow.agent.providers.base import LLMProvider
from forgeflow.observability.metrics import record_llm_call


class InstrumentedLLM:
    """Delegates to an inner provider and records forgeflow.llm.* metrics."""

    def __init__(self, inner: LLMProvider, provider_name: str) -> None:
        self.inner = inner
        self._provider_name = provider_name

    async def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        temperature: float | None = None,
    ) -> BaseModel:
        started = perf_counter()
        ok = False
        try:
            result = await self.inner.complete_structured(
                system=system,
                user=user,
                schema=schema,
                temperature=temperature,
            )
            ok = True
            return result
        finally:
            record_llm_call(self._provider_name, ok, perf_counter() - started)
