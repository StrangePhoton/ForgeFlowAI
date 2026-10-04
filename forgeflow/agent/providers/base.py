"""LLM provider protocol. Graph nodes depend on this, not on SDK clients."""

from typing import Protocol

from pydantic import BaseModel


class LLMProvider(Protocol):
    async def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        temperature: float | None = None,
    ) -> BaseModel: ...
