import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Union
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError, ProviderAuthError, ProviderCreditError, ProviderRateLimitError

class OpenRouterProvider(BaseProvider):
    def __init__(self):
        super().__init__("openrouter")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.proxy = app_config.app_settings.proxy
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
        self._configured = False
        self._setup()

    def _setup(self):
        self.api_key = app_config.api_keys.get("OPENROUTER_API_KEY")
        if self.api_key:
            self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("OpenRouter API key not configured")
            
        model = kwargs.pop("model", "anthropic/claude-3-haiku")
        trace_id = kwargs.pop("trace_id", None)
        return await self._process_request(prompt, model, "text", trace_id=trace_id, **kwargs)

    async def _process_request(self, prompt: str, model: str, content_type: str, trace_id: str = None, **kwargs) -> GenerationResult:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/gemini-cli", 
                "X-Title": "Multimodal AI Studio",
                "Content-Type": "application/json",
                "User-Agent": "MultimodalAIStudio/1.0"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
            }
            
            # Special handling for image generation models
            if content_type == "image":
                payload["modalities"] = ["image"]

            async with httpx.AsyncClient(timeout=60, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                if response.status_code == 401:
                    raise ProviderAuthError(f"OpenRouter Authentication failed: {response.text}")
                elif response.status_code != 200:
                    raise ProviderResponseError(f"OpenRouter Error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                if 'choices' not in data or not data['choices']:
                    raise ProviderResponseError(f"OpenRouter returned unexpected format: {data}")
                    
                content = data['choices'][0]['message']['content']
                
                if not content:
                    raise ProviderResponseError("OpenRouter returned empty content")
                
                # If the response is meant to be a file (URL), handle it
                if content_type in ["image", "audio"]:
                    if content.startswith("http"):
                        media_resp = await client.get(content)
                        return self.create_result(media_resp.content, content_type, model, trace_id=trace_id)
                
                return self.create_result(content, content_type, model, trace_id=trace_id)
        except (ProviderAuthError, ProviderResponseError):
            raise
        except Exception as e:
            self.log_error(f"generate_{content_type}", e, trace_id=trace_id)
            raise ProviderError(f"OpenRouter {content_type} generation failed: {str(e)}") from e

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("OpenRouter API key not configured")
        model = kwargs.pop("model", "black-forest-labs/flux-1-schnell")
        trace_id = kwargs.pop("trace_id", None)
        return await self._process_request(prompt, model, "image", trace_id=trace_id, **kwargs)

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("OpenRouter API key not configured")
        model = kwargs.pop("model", "openai/tts-1")
        trace_id = kwargs.pop("trace_id", None)
        return await self._process_request(prompt, model, "audio", trace_id=trace_id, **kwargs)

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("OpenRouter does not support video generation yet.")

    async def analyze_image(self, image_data: Union[bytes, List[bytes]], prompt: str, **kwargs) -> str:
        if not self.is_configured():
            raise ProviderNotConfigured("OpenRouter API key not configured")
        
        import base64
        trace_id = kwargs.pop("trace_id", None)
        model = kwargs.get("model", app_config.app_settings.openrouter_vision_model)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
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

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": content_parts,
                    }
                ],
                "max_tokens": kwargs.get("max_tokens", 512),
            }
            async with httpx.AsyncClient(timeout=60, transport=self.transport) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                if response.status_code == 401:
                    raise ProviderAuthError(f"OpenRouter Authentication failed: {response.text}")
                elif response.status_code == 402:
                    raise ProviderCreditError("OpenRouter failed: insufficient credits or max_tokens too high. Please add credits or reduce max_tokens.")
                elif response.status_code == 429:
                    raise ProviderRateLimitError(f"OpenRouter Rate Limited (429): {response.text}")
                elif response.status_code != 200:
                     raise ProviderResponseError(f"OpenRouter Vision Error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                if 'choices' not in data or not data['choices']:
                    raise ProviderResponseError(f"OpenRouter Vision returned no choices: {data}")
                
                content = data['choices'][0]['message']['content']
                if not content:
                    raise ProviderResponseError("OpenRouter Vision returned empty content")
                return content
        except Exception as e:
            self.log_error("analyze_image", e, trace_id=trace_id)
            raise ProviderError(f"OpenRouter Vision failed for model {model}: {str(e)}") from e
