import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult
from core.config_loader import ModelConfig

@pytest.mark.asyncio
async def test_image_to_text_route_success():
    orchestrator = AsyncOrchestrator()
    
    # Mock a provider
    mock_gemini = MagicMock()
    mock_gemini.is_configured.return_value = True
    mock_gemini.analyze_image = AsyncMock(return_value="A beautiful landscape")
    
    orchestrator.providers["gemini"] = mock_gemini
    
    # We call generate for image->text
    result = await orchestrator.generate("What is in this image?", input_type="image", output_type="text", image_bytes=b"fake-image")
    
    assert result.provider == "gemini"
    assert result.content == "A beautiful landscape"
    assert result.content_type == "text"
    assert result.input_type == "image"
    assert result.output_type == "text"
    assert result.trace_id is not None

@pytest.mark.asyncio
async def test_image_to_text_fallback():
    orchestrator = AsyncOrchestrator()
    
    # Mock all providers in the chain to control behavior
    mock_gemini = MagicMock()
    mock_gemini.is_configured.return_value = True
    mock_gemini.analyze_image = AsyncMock(side_effect=Exception("Gemini Vision Failed"))
    
    mock_openrouter = MagicMock()
    mock_openrouter.is_configured.return_value = True
    mock_openrouter.analyze_image = AsyncMock(side_effect=Exception("OpenRouter Vision Failed"))
    
    mock_hf = MagicMock()
    mock_hf.is_configured.return_value = True
    mock_hf.analyze_image = AsyncMock(return_value="A successful fallback")
    
    orchestrator.providers["gemini"] = mock_gemini
    orchestrator.providers["openrouter"] = mock_openrouter
    orchestrator.providers["huggingface"] = mock_hf
    
    # The chain in config is Gemini -> OpenRouter -> HuggingFace
    result = await orchestrator.generate("Describe the image", input_type="image", output_type="text", image_bytes=b"fake-image")
    
    assert result.provider == "huggingface"
    assert result.content == "A successful fallback"
    assert result.fallback_used is True
    assert len(result.failed_providers) == 2
    assert result.failed_providers[0]["provider"] == "gemini"
    assert result.failed_providers[1]["provider"] == "openrouter"
