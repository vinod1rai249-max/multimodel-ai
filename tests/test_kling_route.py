import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult

@pytest.fixture
def clean_orchestrator():
    # Helper to create an orchestrator with mocked providers to avoid actual init noise
    with patch('providers.gemini.GeminiProvider', MagicMock()), \
         patch('providers.groq.GroqProvider', MagicMock()), \
         patch('providers.huggingface.HuggingFaceProvider', MagicMock()), \
         patch('providers.openrouter.OpenRouterProvider', MagicMock()), \
         patch('providers.edge_tts.EdgeTTSProvider', MagicMock()), \
         patch('providers.google_tts.GoogleTTSProvider', MagicMock()), \
         patch('providers.gtts_provider.GTTSProvider', MagicMock()), \
         patch('providers.elevenlabs.ElevenLabsProvider', MagicMock()), \
         patch('providers.pollinations.PollinationsProvider', MagicMock()), \
         patch('providers.pexels.PexelsProvider', MagicMock()), \
         patch('providers.replicate.ReplicateProvider', MagicMock()), \
         patch('providers.kling.KlingProvider', MagicMock()):
         return AsyncOrchestrator()

@pytest.mark.asyncio
async def test_kling_registered_when_conditions_met(monkeypatch):
    # Condition: Key exists AND provider is kling
    with patch('core.config_loader.config.api_keys', {"KLING_API_KEY": "test-key"}):
        with patch('core.config_loader.config.app_settings.image_to_video_provider', "kling"):
             with patch('providers.kling.KlingProvider', MagicMock()):
                orchestrator = AsyncOrchestrator()
                assert "kling" in orchestrator.providers

@pytest.mark.asyncio
async def test_kling_skipped_when_key_missing():
    # Condition: Key missing
    with patch('core.config_loader.config.api_keys', {"KLING_API_KEY": None}):
        with patch('core.config_loader.config.app_settings.image_to_video_provider', "kling"):
            orchestrator = AsyncOrchestrator()
            assert "kling" not in orchestrator.providers

@pytest.mark.asyncio
async def test_kling_skipped_when_not_selected():
    # Condition: Provider is NOT kling
    with patch('core.config_loader.config.api_keys', {"KLING_API_KEY": "test-key"}):
        with patch('core.config_loader.config.app_settings.image_to_video_provider', "replicate"):
            orchestrator = AsyncOrchestrator()
            assert "kling" not in orchestrator.providers

@pytest.mark.asyncio
async def test_image_to_video_priority_order(clean_orchestrator):
    # Mock vision
    mock_vision = MagicMock()
    mock_vision.is_configured.return_value = True
    mock_vision.analyze_image = AsyncMock(return_value="Caption")
    clean_orchestrator.providers["gemini"] = mock_vision
    
    # Mock Kling (should be first)
    mock_kling = MagicMock()
    mock_kling.is_configured.return_value = True
    mock_kling.generate_video = AsyncMock(return_value=GenerationResult(
        provider="kling", model="v3", content=b"kling-vid", content_type="video", metadata={"is_real_video": True}
    ))
    clean_orchestrator.providers["kling"] = mock_kling
    
    # Mock Replicate (should be second)
    mock_replicate = MagicMock()
    mock_replicate.is_configured.return_value = True
    mock_replicate.generate_video = AsyncMock(return_value=GenerationResult(
        provider="replicate", model="svd", content=b"repl-vid", content_type="video", metadata={"is_real_video": True}
    ))
    clean_orchestrator.providers["replicate"] = mock_replicate
    
    result = await clean_orchestrator.generate("Test", input_type="image", output_type="video", image_bytes=b"fake")
    
    assert result.provider == "kling"
    assert result.content_type == "video"
    assert result.metadata.get("is_real_video") is True

@pytest.mark.asyncio
async def test_storyboard_fallback_metadata(clean_orchestrator):
    # Mock vision
    mock_vision = MagicMock()
    mock_vision.is_configured.return_value = True
    mock_vision.analyze_image = AsyncMock(return_value="Caption")
    clean_orchestrator.providers["gemini"] = mock_vision
    
    # All video providers fail
    for p in ["kling", "replicate"]:
        mock = MagicMock()
        mock.is_configured.return_value = True
        mock.generate_video = AsyncMock(side_effect=Exception("Fail"))
        clean_orchestrator.providers[p] = mock
        
    # Mock Groq for storyboard
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = True
    mock_groq.generate_text = AsyncMock(return_value=GenerationResult(
        provider="groq", model="llama", content="Scene 1", content_type="text"
    ))
    clean_orchestrator.providers["groq"] = mock_groq
    
    result = await clean_orchestrator.generate("Test", input_type="image", output_type="video", image_bytes=b"fake")
    
    assert result.content_type == "storyboard"
    assert result.metadata.get("is_real_video") is False
    assert result.provider == "groq"
    assert result.model == "llama"
    assert result.trace_id is not None
