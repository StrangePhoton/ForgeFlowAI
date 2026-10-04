"""LLM provider factory and mock behavior. Default tests never call a paid API."""

import pytest
from forgeflow.agent.models import RequestAnalysis
from forgeflow.agent.providers.factory import create_llm_provider
from forgeflow.agent.providers.mock import MockLLMProvider
from forgeflow.agent.providers.ollama import OllamaProvider
from forgeflow.agent.providers.openai import OpenAIProvider
from forgeflow.config import Settings
from forgeflow.errors import ProviderError, StructuredOutputError
from pydantic import BaseModel


@pytest.mark.asyncio
async def test_mock_provider_extracts_cnc_code() -> None:
    provider = MockLLMProvider()
    analysis = await provider.complete_structured(
        system="sys",
        user="Please investigate overheating on CNC-042",
        schema=RequestAnalysis,
    )
    assert isinstance(analysis, RequestAnalysis)
    assert analysis.equipment_code == "CNC-042"


@pytest.mark.asyncio
async def test_mock_provider_rejects_unknown_schema() -> None:
    class Other(BaseModel):
        value: str

    provider = MockLLMProvider()
    with pytest.raises(StructuredOutputError):
        await provider.complete_structured(system="sys", user="x", schema=Other)


def test_factory_selects_mock_openai_and_ollama() -> None:
    mock = create_llm_provider(Settings.model_validate({"llm_provider": "mock"}))
    assert isinstance(mock, MockLLMProvider)
    ollama = create_llm_provider(
        Settings.model_validate(
            {"llm_provider": "ollama", "llm_api_base": "http://127.0.0.1:11434"}
        )
    )
    assert isinstance(ollama, OllamaProvider)
    with pytest.raises(ProviderError):
        create_llm_provider(Settings.model_validate({"llm_provider": "openai"}))
    openai = create_llm_provider(
        Settings.model_validate({"llm_provider": "openai", "llm_api_key": "sk-test"})
    )
    assert isinstance(openai, OpenAIProvider)
