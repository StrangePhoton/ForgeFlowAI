"""Ollama HTTP adapter with JSON-schema formatted responses."""

import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from forgeflow.config import Settings
from forgeflow.errors import ProviderError, StructuredOutputError

_DEFAULT_OLLAMA_BASE = "http://localhost:11434"


class OllamaProvider:
    """Calls a local Ollama /api/chat endpoint. No paid API is used."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = (settings.llm_api_base or _DEFAULT_OLLAMA_BASE).rstrip("/")
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._timeout = settings.llm_timeout_seconds
        self._max_retries = settings.llm_max_retries

    async def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        temperature: float | None = None,
    ) -> BaseModel:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {"temperature": self._temperature if temperature is None else temperature},
        }
        last_error: Exception | None = None
        attempts = self._max_retries + 1
        for _attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(f"{self._base_url}/api/chat", json=body)
                response.raise_for_status()
                payload = response.json()
                content = payload.get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    raise StructuredOutputError("Ollama returned an empty message")
                return schema.model_validate_json(content)
            except (
                httpx.HTTPError,
                json.JSONDecodeError,
                ValidationError,
                StructuredOutputError,
            ) as exc:
                last_error = exc
                continue
        raise ProviderError("Ollama request failed") from last_error
