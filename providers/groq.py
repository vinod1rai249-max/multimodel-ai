from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError
from groq import Groq
import os
import asyncio
import base64
from typing import List, Dict, Any, Optional, Union
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
import httpx

class GroqProvider(BaseProvider):
    def __init__(self):
        super().__init__("groq")
        self._configured = False
        self.client = None
        self._setup()

    def _setup(self):
        api_key = app_config.api_keys.get("GROQ_API_KEY")
        if api_key:
            try:
                # Force IPv4 via custom httpx client for Groq SDK
                http_client = httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))
                self.client = Groq(api_key=api_key, http_client=http_client)
                self._configured = True
            except Exception as e:
                app_logger.error(f"Failed to initialize Groq client: {e}")
                self._configured = False

    def is_configured(self) -> bool:
        return self._configured

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("Groq API key not configured")
        
        model = kwargs.pop("model", app_config.app_settings.text_model_groq)
        trace_id = kwargs.pop("trace_id", None)
        
        try:
            return await self._execute_request(prompt, model, trace_id=trace_id, **kwargs)
        except Exception as e:
            self.log_error("generate_text", e, trace_id=trace_id)
            raise ProviderError(f"Groq failed: {str(e)}") from e

    async def _execute_request(self, prompt: str, model_id: str, trace_id: str = None, **kwargs) -> GenerationResult:
        messages = [{"role": "user", "content": prompt}]
        completion = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=model_id,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        )
        if not completion or not completion.choices[0].message.content:
            raise ProviderResponseError("Groq returned an empty response")
        return self.create_result(completion.choices[0].message.content, "text", model_id, trace_id=trace_id)

    async def analyze_image(self, image_data: Union[bytes, List[bytes]], prompt: str, **kwargs) -> str:
        if not self.is_configured():
            raise ProviderNotConfigured("Groq API key not configured")
        
        trace_id = kwargs.get("trace_id")
        # For Groq, we don't have a specific vision model in AppSettings yet, 
        # but it's passed from config.routing.
        model = kwargs.get("model", "llama-3.2-11b-vision-preview")
        
        try:
            content_parts = [{"type": "text", "text": prompt}]
            
            if isinstance(image_data, list):
                for img_bytes in image_data:
                    base64_image = base64.b64encode(img_bytes).decode('utf-8')
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                        },
                    })
            else:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                    },
                })

            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": content_parts,
                    }
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.log_error("analyze_image", e, trace_id=trace_id)
            raise ProviderError(f"Groq Vision failed: {str(e)}") from e
