from core.interfaces import IProvider, GenerationResult
from core.logger import app_logger
from abc import ABC

class BaseProvider(IProvider, ABC):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def log_error(self, method: str, error: Exception):
        # Professional Forensic Logging: Type, Message, and Context
        error_type = type(error).__name__
        msg = f"❌ [FORENSIC] Provider '{self.provider_name}' FAILED in '{method}' | Type: {error_type} | Message: {str(error)}"
        app_logger.error(msg)
        # Log the detailed error for technical analysis
        app_logger.debug(f"FULL TRACEBACK for {self.provider_name}:\n", exc_info=error)

    def create_result(self, content: any, content_type: str, model: str, metadata: dict = {}) -> GenerationResult:
        return GenerationResult(
            provider=self.provider_name,
            model=model,
            content=content,
            content_type=content_type,
            metadata=metadata
        )

    async def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> str:
        raise NotImplementedError(f"Provider {self.provider_name} does not support image analysis.")
