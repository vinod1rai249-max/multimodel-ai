import yaml
import os
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

class AppSettings(BaseModel):
    theme: str = "dark"
    cache_dir: str = "./cache"
    max_history_len: int = 20
    log_level: str = "INFO"
    proxy: Optional[str] = None

class Config(BaseModel):
    routing: RoutingConfig
    app_settings: AppSettings

def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    
    return Config(**data)

# Singleton instance
config = load_config()
