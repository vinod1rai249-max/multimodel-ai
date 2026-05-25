import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult
from core.config_loader import ModelConfig
from core.errors import AllProvidersFailedError, UnsupportedRouteError

@pytest.fixture
def orchestrator():
    return AsyncOrchestrator()

@pytest.mark.asyncio
async def test_orchestrator_fallback_success(orchestrator):
    # Mock providers
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = True
    mock_groq.generate_text = AsyncMock(side_effect=Exception("Groq Failed"))
    
    mock_gemini = MagicMock()
    mock_gemini.is_configured.return_value = True
    mock_gemini.generate_text = AsyncMock(return_value=GenerationResult(
        provider="gemini",
        model="gemini-1.5",
        content="Success from Gemini",
        content_type="text"
    ))
    
    orchestrator.providers["groq"] = mock_groq
    orchestrator.providers["gemini"] = mock_gemini
    
    chain = [
        ModelConfig(provider="groq", model="q-1"),
        ModelConfig(provider="gemini", model="g-1")
    ]
    
    result = await orchestrator._execute_with_fallback(chain, "generate_text", "hello", "trace-123")
    
    assert result.provider == "gemini"
    assert result.content == "Success from Gemini"
    assert result.fallback_used is True
    assert len(result.failed_providers) == 1
    assert result.failed_providers[0]["provider"] == "groq"

@pytest.mark.asyncio
async def test_orchestrator_not_configured_skip(orchestrator):
    # Mock providers
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = False # Not configured
    
    mock_gemini = MagicMock()
    mock_gemini.is_configured.return_value = True
    mock_gemini.generate_text = AsyncMock(return_value=GenerationResult(
        provider="gemini",
        model="gemini-1.5",
        content="Success from Gemini",
        content_type="text"
    ))
    
    orchestrator.providers["groq"] = mock_groq
    orchestrator.providers["gemini"] = mock_gemini
    
    chain = [
        ModelConfig(provider="groq", model="q-1"),
        ModelConfig(provider="gemini", model="g-1")
    ]
    
    result = await orchestrator._execute_with_fallback(chain, "generate_text", "hello", "trace-123")
    
    assert result.provider == "gemini"
    assert result.fallback_used is True
    assert result.failed_providers[0]["error"] == "NotConfigured"

@pytest.mark.asyncio
async def test_orchestrator_all_fail(orchestrator):
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = True
    mock_groq.generate_text = AsyncMock(side_effect=Exception("Fatal Error"))
    orchestrator.providers["groq"] = mock_groq
    
    chain = [ModelConfig(provider="groq", model="q-1")]
    
    with pytest.raises(AllProvidersFailedError):
        await orchestrator._execute_with_fallback(chain, "generate_text", "hello", "trace-123")

@pytest.mark.asyncio
async def test_unsupported_route(orchestrator):
    with pytest.raises(UnsupportedRouteError):
        await orchestrator.generate("hello", input_type="text", output_type="hologram")

@pytest.mark.asyncio
async def test_text_to_text_route_metadata(orchestrator):
    # Mock success for Groq
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = True
    mock_groq.generate_text = AsyncMock(return_value=GenerationResult(
        provider="groq",
        model="llama-3",
        content="Hello world",
        content_type="text"
    ))
    orchestrator.providers["groq"] = mock_groq
    
    result = await orchestrator.generate("hi", input_type="text", output_type="text")
    
    assert result.provider == "groq"
    assert result.content_type == "text"
    assert result.trace_id is not None
    assert isinstance(result.failed_providers, list)
