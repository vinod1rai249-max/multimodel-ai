import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.orchestrator import AsyncOrchestrator
from core.interfaces import GenerationResult

@pytest.fixture
def orchestrator():
    return AsyncOrchestrator()

@pytest.mark.asyncio
async def test_video_to_text_pipeline(orchestrator):
    # Mock video bytes
    mock_video_bytes = b"fake video data"
    
    # Mock extract_key_frames
    mock_frames = [b"frame1", b"frame2"]
    
    with patch("core.orchestrator.extract_key_frames", return_value=mock_frames) as mock_extract:
        # Mock Gemini Vision
        mock_gemini = MagicMock()
        mock_gemini.is_configured.return_value = True
        mock_gemini.analyze_image = AsyncMock(return_value="Detailed video description")
        orchestrator.providers["gemini"] = mock_gemini
        
        result = await orchestrator.generate(
            prompt="Analyze this video",
            input_type="video",
            output_type="text",
            video_bytes=mock_video_bytes
        )
        
        # Verify extract_key_frames was called
        mock_extract.assert_called_once_with(mock_video_bytes, interval_seconds=2, max_frames=8)
        
        # Verify Gemini was called with frames
        mock_gemini.analyze_image.assert_called_once()
        args, kwargs = mock_gemini.analyze_image.call_args
        assert args[0] == mock_frames
        assert args[1] == "Analyze this video"
        
        assert result.content == "Detailed video description"
        assert result.metadata["total_frames_extracted"] == 2
        assert result.metadata["route"] == "Video → Text"

@pytest.mark.asyncio
async def test_video_to_text_empty_bytes(orchestrator):
    with pytest.raises(Exception) as exc:
        await orchestrator.generate(
            prompt="Analyze this",
            input_type="video",
            output_type="text",
            video_bytes=None
        )
    assert "No video uploaded" in str(exc.value)

@pytest.mark.asyncio
async def test_video_to_text_extraction_failure(orchestrator):
    with patch("core.orchestrator.extract_key_frames", return_value=[]):
        with pytest.raises(Exception) as exc:
            await orchestrator.generate(
                prompt="Analyze this",
                input_type="video",
                output_type="text",
                video_bytes=b"corrupt data"
            )
        assert "Failed to extract frames" in str(exc.value)
