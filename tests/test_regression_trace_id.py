import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult
from core.config_loader import ModelConfig

@pytest.mark.asyncio
async def test_groq_fallback_no_duplicate_trace_id():
    orchestrator = AsyncOrchestrator()
    
    # Mock Groq to fail, then Gemini to succeed
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
    
    # We call generate, which creates its own trace_id but might receive one in kwargs
    kwargs = {"trace_id": "upstream-id", "temperature": 0.9}
    
    # This should NOT raise TypeError
    result = await orchestrator.generate("hello", input_type="text", output_type="text", **kwargs)
    
    assert result.provider == "gemini"
    assert result.fallback_used is True
    assert len(result.failed_providers) == 1
    assert result.failed_providers[0]["provider"] == "groq"

@pytest.mark.asyncio
async def test_failed_providers_metadata_structure():
    orchestrator = AsyncOrchestrator()
    
    # Mock ALL providers to fail
    for p_name in orchestrator.providers:
        mock_p = MagicMock()
        mock_p.is_configured.return_value = True
        mock_p.generate_text = AsyncMock(side_effect=Exception(f"{p_name} Failed"))
        orchestrator.providers[p_name] = mock_p
    
    # Call generate directly
    from core.errors import AllProvidersFailedError
    with pytest.raises(AllProvidersFailedError) as excinfo:
        await orchestrator.generate("hello", input_type="text", output_type="text")
    
    failures = excinfo.value.failures
    assert len(failures) >= 1
    assert failures[0]["provider"] == "groq" # First in text chain
    assert "groq Failed" in failures[0]["message"]
    assert isinstance(failures[0], dict)
