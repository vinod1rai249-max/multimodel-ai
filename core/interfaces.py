from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class GenerationResult(BaseModel):
    provider: str
    model: str
    content: Any  # Can be string (text) or bytes (media)
    metadata: Dict[str, Any] = {}
    content_type: str  # "text", "image", "audio", "video"
    fallback_used: bool = False
    failed_providers: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None
    latency: float = 0.0
    input_type: Optional[str] = None
    output_type: Optional[str] = None

class IProvider(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured (e.g., API keys)."""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        pass

    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        pass

    @abstractmethod
    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        pass

    @abstractmethod
    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        pass

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> str:
        pass
