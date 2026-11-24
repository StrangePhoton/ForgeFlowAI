"""Select an LLM provider from application settings."""

from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.providers.mock import MockLLMProvider
from forgeflow.agent.providers.ollama import OllamaProvider
from forgeflow.agent.providers.openai import OpenAIProvider
from forgeflow.config import Settings
from forgeflow.errors import ProviderError
from forgeflow.observability.llm import InstrumentedLLM


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        inner: LLMProvider = MockLLMProvider()
    elif settings.llm_provider == "openai":
        inner = OpenAIProvider(settings)
    elif settings.llm_provider == "ollama":
        inner = OllamaProvider(settings)
    else:
        raise ProviderError(f"Unsupported LLM provider {settings.llm_provider}")
    return InstrumentedLLM(inner, settings.llm_provider)
