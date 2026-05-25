import pytest
import os
from core.config_loader import load_config, Config

def test_config_centralized_models():
    # Mock environment variables
    os.environ["GEMINI_VISION_MODEL"] = "gemini-test-vision"
    os.environ["VIDEO_TEXT_GEMINI_MODEL"] = "video-test-gemini"
    os.environ["OPENROUTER_VISION_MODEL"] = "openrouter-test-vision"
    os.environ["HF_VISION_MODEL"] = "hf-test-vision"
    os.environ["TEXT_MODEL_GROQ"] = "groq-test-text"
    os.environ["IMAGE_TO_VIDEO_PROVIDER"] = "replicate"
    os.environ["KLING_IMAGE_TO_VIDEO_MODEL"] = "kling-test-video"
    os.environ["REPLICATE_IMAGE_TO_VIDEO_MODEL"] = "replicate/test-model:v1"
    
    # Reload config
    cfg = load_config()
    
    assert cfg.app_settings.gemini_vision_model == "gemini-test-vision"
    assert cfg.app_settings.video_text_gemini_model == "video-test-gemini"
    assert cfg.app_settings.openrouter_vision_model == "openrouter-test-vision"
    assert cfg.app_settings.hf_vision_model == "hf-test-vision"
    assert cfg.app_settings.text_model_groq == "groq-test-text"
    assert cfg.app_settings.image_to_video_provider == "replicate"
    assert cfg.app_settings.kling_image_to_video_model == "kling-test-video"
    assert cfg.app_settings.replicate_image_to_video_model == "replicate/test-model:v1"
    
    # Check routing objects
    # Image to text should have 3 items matching these
    providers = {m.provider: m.model for m in cfg.routing.image_to_text}
    assert providers["gemini"] == "gemini-test-vision"
    assert providers["openrouter"] == "openrouter-test-vision"
    assert providers["huggingface"] == "hf-test-vision"
    
    # Video to text
    v_providers = {m.provider: m.model for m in cfg.routing.video_to_text}
    assert v_providers["gemini"] == "video-test-gemini"
    
    # Video generation
    g_providers = {m.provider: m.model for m in cfg.routing.video_generation}
    assert g_providers["kling"] == "kling-test-video"
    assert g_providers["replicate"] == "replicate/test-model:v1"

    # Cleanup
    del os.environ["GEMINI_VISION_MODEL"]
    del os.environ["VIDEO_TEXT_GEMINI_MODEL"]
    del os.environ["OPENROUTER_VISION_MODEL"]
    del os.environ["HF_VISION_MODEL"]
    del os.environ["TEXT_MODEL_GROQ"]
    del os.environ["IMAGE_TO_VIDEO_PROVIDER"]
    del os.environ["KLING_IMAGE_TO_VIDEO_MODEL"]
    del os.environ["REPLICATE_IMAGE_TO_VIDEO_MODEL"]
