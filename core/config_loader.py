from dotenv import load_dotenv

# Load environment variables at the very top
load_dotenv()

import yaml
import os
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ModelConfig(BaseModel):
    provider: str
    model: str
    timeout: int = 30

class RoutingConfig(BaseModel):
    text_generation: List[ModelConfig]
    image_generation: List[ModelConfig]
    audio_generation: List[ModelConfig]
    video_generation: List[ModelConfig]
    image_to_text: List[ModelConfig]
    video_to_text: List[ModelConfig] = Field(default_factory=list)

class AppSettings(BaseModel):
    theme: str = "dark"
    cache_dir: str = "./cache"
    max_history_len: int = 20
    log_level: str = "INFO"
    proxy: Optional[str] = None
    image_to_video_provider: str = "kling"
    kling_image_to_video_model: str = "kling-v3-video"
    replicate_image_to_video_model: str = "stability-ai/stable-video-diffusion:ac732d8354fd18dbbf3c9d61458a0ad37a22f77e682247b97f51f11e967a6e60"
    gemini_vision_model: str = "gemini-2.0-flash"
    video_text_gemini_model: str = "gemini-2.0-flash"
    openrouter_vision_model: str = "qwen/qwen2.5-vl-72b-instruct"
    hf_vision_model: str = "Salesforce/blip-image-captioning-base"
    text_model_groq: str = "llama-3.3-70b-versatile"

class Config(BaseModel):
    routing: RoutingConfig
    app_settings: AppSettings
    api_keys: Dict[str, str] = Field(default_factory=dict)

def get_config_value(key_name: str, default: Any = None) -> Any:
    # 1. Try Streamlit Secrets
    val = None
    try:
        if key_name in st.secrets:
            val = st.secrets[key_name]
    except Exception:
        pass
    
    # 2. Try Environment Variables
    if val is None:
        val = os.getenv(key_name)
        
    if val is None or not isinstance(val, str) or val.strip() == "" or val.lower() in ["your_key", "your_api_key_here", "placeholder", "your_gemini_key", "your_openrouter_key", "your_model_here"]:
        return default
    return val.strip()

def get_api_key(key_name: str) -> Optional[str]:
    return get_config_value(key_name)

def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    
    config_obj = Config(**data)
    
    # Load API keys
    keys_to_load = [
        "GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", 
        "HF_TOKEN", "PEXELS_API_KEY", "ELEVENLABS_API_KEY", 
        "GOOGLE_APPLICATION_CREDENTIALS", "REPLICATE_API_TOKEN",
        "KLING_API_KEY"
    ]
    
    config_obj.api_keys = {key: get_api_key(key) for key in keys_to_load}
    
    # Load app settings overrides from ENV
    config_obj.app_settings.image_to_video_provider = get_config_value("IMAGE_TO_VIDEO_PROVIDER", config_obj.app_settings.image_to_video_provider)
    config_obj.app_settings.kling_image_to_video_model = get_config_value("KLING_IMAGE_TO_VIDEO_MODEL", config_obj.app_settings.kling_image_to_video_model)
    config_obj.app_settings.replicate_image_to_video_model = get_config_value("REPLICATE_IMAGE_TO_VIDEO_MODEL", config_obj.app_settings.replicate_image_to_video_model)
    config_obj.app_settings.gemini_vision_model = get_config_value("GEMINI_VISION_MODEL", config_obj.app_settings.gemini_vision_model)
    config_obj.app_settings.video_text_gemini_model = get_config_value("VIDEO_TEXT_GEMINI_MODEL", config_obj.app_settings.video_text_gemini_model)
    config_obj.app_settings.openrouter_vision_model = get_config_value("OPENROUTER_VISION_MODEL", config_obj.app_settings.openrouter_vision_model)
    config_obj.app_settings.hf_vision_model = get_config_value("HF_VISION_MODEL", config_obj.app_settings.hf_vision_model)
    config_obj.app_settings.text_model_groq = get_config_value("TEXT_MODEL_GROQ", config_obj.app_settings.text_model_groq)

    # Rebuild routing based on synchronized settings
    # 1. Text Generation
    for m in config_obj.routing.text_generation:
        if m.provider == "groq":
            m.model = config_obj.app_settings.text_model_groq

    # 2. Image to Text
    config_obj.routing.image_to_text = [
        ModelConfig(provider="gemini", model=config_obj.app_settings.gemini_vision_model),
        ModelConfig(provider="openrouter", model=config_obj.app_settings.openrouter_vision_model),
        ModelConfig(provider="huggingface", model=config_obj.app_settings.hf_vision_model)
    ]

    # 3. Video to Text
    config_obj.routing.video_to_text = [
        ModelConfig(provider="gemini", model=config_obj.app_settings.video_text_gemini_model),
        ModelConfig(provider="openrouter", model=config_obj.app_settings.openrouter_vision_model),
        ModelConfig(provider="huggingface", model=config_obj.app_settings.hf_vision_model)
    ]

    # 4. Video Generation (Text/Image to Video)
    for m in config_obj.routing.video_generation:
        if m.provider == "kling":
            m.model = config_obj.app_settings.kling_image_to_video_model
        if m.provider == "replicate":
            m.model = config_obj.app_settings.replicate_image_to_video_model

    # Startup Diagnostics
    print("\n" + "="*50)
    print("🚀 MULTIMODAL AI STUDIO - STARTUP DIAGNOSTICS")
    print("="*50)
    print(f"🔹 Gemini Vision Model:      {config_obj.app_settings.gemini_vision_model}")
    print(f"🔹 Video-Text Gemini:        {config_obj.app_settings.video_text_gemini_model}")
    print(f"🔹 OpenRouter Vision:        {config_obj.app_settings.openrouter_vision_model}")
    print(f"🔹 HF Vision Model:          {config_obj.app_settings.hf_vision_model}")
    print(f"🔹 Image-to-Video Provider:  {config_obj.app_settings.image_to_video_provider.upper()}")
    print(f"🔹 Kling Configured:         {'✅ YES' if config_obj.api_keys.get('KLING_API_KEY') else '❌ NO'}")
    print(f"🔹 Replicate Configured:     {'✅ YES' if config_obj.api_keys.get('REPLICATE_API_TOKEN') else '❌ NO'}")
    
    # Check Replicate model format
    repl_model = config_obj.app_settings.replicate_image_to_video_model
    if repl_model and ":" not in repl_model:
        print(f"⚠️  WARNING: Replicate model '{repl_model}' format invalid (missing :version)")
    
    print("="*50 + "\n")

    return config_obj

# Singleton instance
config = load_config()
