from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class GenerationResult(BaseModel):
    provider: str
    model: str
    content: Any  # Can be string (text) or bytes (media)
    metadata: Dict[str, Any] = {}
    content_type: str  # "text", "image", "audio", "video"

class IProvider(ABC):
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
