"""OpenAI chat completions adapter with Pydantic structured outputs."""

from openai import APIError, AsyncOpenAI
from pydantic import BaseModel

from forgeflow.config import Settings
from forgeflow.errors import ProviderError, StructuredOutputError


class OpenAIProvider:
    """OpenAI-compatible client. Azure can reuse this with a different base URL."""

    def __init__(self, settings: Settings) -> None:
        if not settings.llm_api_key:
            raise ProviderError("LLM_API_KEY is required when LLM_PROVIDER=openai")
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature

    async def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        temperature: float | None = None,
    ) -> BaseModel:
        try:
            completion = await self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=schema,
                temperature=self._temperature if temperature is None else temperature,
            )
        except APIError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        except Exception as exc:
            raise ProviderError("OpenAI request failed") from exc
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise StructuredOutputError("OpenAI returned no parsed object")
        return schema.model_validate(parsed.model_dump())
