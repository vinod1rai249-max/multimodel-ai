from core.interfaces import IProvider, GenerationResult
from core.logger import app_logger
from abc import ABC
from typing import Any, List, Union

class BaseProvider(IProvider, ABC):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def log_error(self, method: str, error: Exception, trace_id: str = None):
        # Professional Forensic Logging: Type, Message, and Context
        error_type = type(error).__name__
        extra = {"trace_id": trace_id, "provider": self.provider_name, "method": method, "error_type": error_type}
        msg = f"❌ [FORENSIC] Provider '{self.provider_name}' FAILED in '{method}' | Type: {error_type} | Message: {str(error)}"
        app_logger.bind(**extra).error(msg)
        # Log the detailed error for technical analysis
        app_logger.bind(**extra).debug(f"FULL TRACEBACK for {self.provider_name}:\n", exc_info=error)

    def create_result(self, content: Any, content_type: str, model: str, metadata: dict = {}, trace_id: str = None) -> GenerationResult:
        return GenerationResult(
            provider=self.provider_name,
            model=model,
            content=content,
            content_type=content_type,
            metadata=metadata,
            trace_id=trace_id
        )

    def is_configured(self) -> bool:
        # Default implementation, should be overridden by providers that need keys
        return True

    async def analyze_image(self, image_data: Union[bytes, List[bytes]], prompt: str, **kwargs) -> str:
        raise NotImplementedError(f"Provider {self.provider_name} does not support image analysis.")

    # Default implementations that raise NotImplementedError
    async def generate_text(self, prompt: str, history: list = [], **kwargs) -> GenerationResult:
        raise NotImplementedError(f"Provider {self.provider_name} does not support text generation.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError(f"Provider {self.provider_name} does not support image generation.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError(f"Provider {self.provider_name} does not support audio generation.")

    async def generate_video(self, prompt: str, image_bytes: bytes = None, **kwargs) -> GenerationResult:
        raise NotImplementedError(f"Provider {self.provider_name} does not support video generation.")
