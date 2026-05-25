import httpx
import asyncio
import os
import urllib.parse
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.config_loader import config as app_config
from core.logger import app_logger
from core.errors import ProviderError, ProviderResponseError

class PollinationsProvider(BaseProvider):
    def __init__(self):
        super().__init__("pollinations")
        self.base_url = "https://image.pollinations.ai/prompt/"
        self.proxy = app_config.app_settings.proxy
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

    def is_configured(self) -> bool:
        return True # Publicly available

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        trace_id = kwargs.get("trace_id")
        encoded_prompt = urllib.parse.quote(prompt)
        
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        seed = kwargs.get("seed", os.urandom(4).hex())
        model = kwargs.get("model", "flux")
        
        url = f"{self.base_url}{encoded_prompt}?width={width}&height={height}&seed={seed}&model={model}&nologo=true"
        
        try:
            async with httpx.AsyncClient(timeout=60, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    raise ProviderResponseError(f"Pollinations Error: {response.status_code}")
                return self.create_result(response.content, "image", model, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_image", e, trace_id=trace_id)
            raise ProviderError(f"Pollinations image failed: {str(e)}") from e

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        trace_id = kwargs.get("trace_id")
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Use specific animation model flag
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=512&model=flux&seed=123&nologo=true&enhance=true"
        
        try:
            async with httpx.AsyncClient(timeout=60, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                app_logger.bind(trace_id=trace_id).info(f"Triggering Pollinations Video for: {prompt}")
                response = await client.get(url)
                if response.status_code != 200:
                    raise ProviderResponseError(f"Pollinations Video Error: {response.status_code}")
                
                return self.create_result(response.content, "video", "pollinations-flux-video", trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_video", e, trace_id=trace_id)
            raise ProviderError(f"Pollinations video failed: {str(e)}") from e
