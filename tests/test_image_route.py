import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult

@pytest.mark.asyncio
async def test_text_to_image_route_success():
    orchestrator = AsyncOrchestrator()
    
    # Mock Pollinations (first in chain)
    mock_pollinations = MagicMock()
    mock_pollinations.is_configured.return_value = True
    mock_pollinations.generate_image = AsyncMock(return_value=GenerationResult(
        provider="pollinations",
        model="flux",
        content=b"fake-image-bytes",
        content_type="image"
    ))
    
    orchestrator.providers["pollinations"] = mock_pollinations
    
    result = await orchestrator.generate("A futuristic city", input_type="text", output_type="image")
    
    assert result.provider == "pollinations"
    assert result.content_type == "image"
    assert result.fallback_used is False

@pytest.mark.asyncio
async def test_text_to_image_fallback():
    orchestrator = AsyncOrchestrator()
    
    # Mock Pollinations to fail
    mock_pollinations = MagicMock()
    mock_pollinations.is_configured.return_value = True
    mock_pollinations.generate_image = AsyncMock(side_effect=Exception("Pollinations Down"))
    
    # Mock HuggingFace to succeed
    mock_hf = MagicMock()
    mock_hf.is_configured.return_value = True
    mock_hf.generate_image = AsyncMock(return_value=GenerationResult(
        provider="huggingface",
        model="sdxl",
        content=b"hf-image-bytes",
        content_type="image"
    ))
    
    orchestrator.providers["pollinations"] = mock_pollinations
    orchestrator.providers["huggingface"] = mock_hf
    
    result = await orchestrator.generate("A sunset over mountains", input_type="text", output_type="image")
    
    assert result.provider == "huggingface"
    assert result.fallback_used is True
    assert len(result.failed_providers) == 1
    assert result.failed_providers[0]["provider"] == "pollinations"
