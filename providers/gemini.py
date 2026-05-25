import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai
import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError, ProviderQuotaError, ProviderAuthError, ProviderRateLimitError

class GeminiProvider(BaseProvider):
    def __init__(self):
        super().__init__("gemini")
        self._configured = False
        self._setup()

    def _setup(self):
        api_key = app_config.api_keys.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self._configured = True
            # Use a sensible default if not provided by config
            self.default_model = "models/gemini-1.5-flash"
        else:
            self.default_model = None

    def is_configured(self) -> bool:
        return self._configured

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured(f"Gemini API key not configured")
        
        model_id = kwargs.pop("model", self.default_model)
        if "models/" not in model_id:
            model_id = f"models/{model_id}"
        
        trace_id = kwargs.pop("trace_id", None)
        
        try:
            return await self._execute_request(prompt, model_id, trace_id=trace_id, **kwargs)
        except Exception as e:
            self.log_error("generate_text", e, trace_id=trace_id)
            raise ProviderError(f"Gemini failed: {str(e)}") from e

    async def _execute_request(self, prompt: str, model_name: str, trace_id: str = None, **kwargs) -> GenerationResult:
        model = genai.GenerativeModel(model_name)
        response = await model.generate_content_async(
            prompt,
            generation_config={
                "temperature": kwargs.get("temperature", 0.7),
                "max_output_tokens": kwargs.get("max_tokens", 2048),
            }
        )
        if not response or not response.text:
             raise ProviderResponseError("Gemini returned an empty response")
        return self.create_result(response.text, "text", model_name, trace_id=trace_id)

    async def analyze_image(self, image_data: Union[bytes, List[bytes]], prompt: str, **kwargs) -> str:
        if not self.is_configured():
            raise ProviderNotConfigured(f"Gemini API key not configured")
        
        # Use model from kwargs or centralized config
        model_id = kwargs.get("model", app_config.app_settings.gemini_vision_model)
        if "models/" not in model_id:
            model_id = f"models/{model_id}"
            
        trace_id = kwargs.get("trace_id")
        
        try:
            model = genai.GenerativeModel(model_id)
            
            # Prepare parts
            parts = [prompt]
            if isinstance(image_data, list):
                for img_bytes in image_data:
                    parts.append({"mime_type": "image/png", "data": img_bytes})
            else:
                parts.append({"mime_type": "image/png", "data": image_data})

            response = await model.generate_content_async(parts)
            
            if not response or not response.text:
                raise ProviderResponseError("Gemini Vision returned an empty response")
                
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                self.log_error("analyze_image", e, trace_id=trace_id)
                raise ProviderRateLimitError(f"Gemini quota/rate limit exceeded: {err_msg}")
            
            if "401" in err_msg or "invalid" in err_msg.lower() and "key" in err_msg.lower():
                self.log_error("analyze_image", e, trace_id=trace_id)
                raise ProviderAuthError(f"Gemini authentication failed: {err_msg}")

            self.log_error("analyze_image", e, trace_id=trace_id)
            raise ProviderError(f"Gemini Vision failed: {str(e)}") from e
