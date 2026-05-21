import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult
from core.config_loader import ModelConfig

@pytest.mark.asyncio
async def test_orchestrator_fallback():
    orchestrator = AsyncOrchestrator()
    
    # Mock providers
    mock_gemini = AsyncMock()
    mock_gemini.generate_text.side_effect = Exception("Gemini Failed")
    
    mock_groq = AsyncMock()
    mock_groq.generate_text.return_value = GenerationResult(
        provider="groq",
        model="llama-3",
        content="Success from Groq",
        content_type="text"
    )
    
    orchestrator.providers["gemini"] = mock_gemini
    orchestrator.providers["groq"] = mock_groq
    
    # Create a simple chain
    chain = [
        ModelConfig(provider="gemini", model="g-1", timeout=5),
        ModelConfig(provider="groq", model="q-1", timeout=5)
    ]
    
    result = await orchestrator._execute_with_fallback(chain, "generate_text", "hello")
    
    assert result.provider == "groq"
    assert result.content == "Success from Groq"
    assert mock_gemini.generate_text.called
    assert mock_groq.generate_text.called

@pytest.mark.asyncio
async def test_orchestrator_all_fail():
    orchestrator = AsyncOrchestrator()
    
    mock_provider = AsyncMock()
    mock_provider.generate_text.side_effect = Exception("Fatal Error")
    orchestrator.providers["gemini"] = mock_provider
    
    chain = [ModelConfig(provider="gemini", model="g-1", timeout=5)]
    
    with pytest.raises(Exception, match="Fatal Error"):
        await orchestrator._execute_with_fallback(chain, "generate_text", "hello")
