"""Select an LLM provider from application settings."""

from forgeflow.agent.providers.base import LLMProvider
from forgeflow.agent.providers.mock import MockLLMProvider
from forgeflow.agent.providers.ollama import OllamaProvider
from forgeflow.agent.providers.openai import OpenAIProvider
from forgeflow.config import Settings
from forgeflow.errors import ProviderError


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings)
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    raise ProviderError(f"Unsupported LLM provider {settings.llm_provider}")
