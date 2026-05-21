import httpx
import asyncio
import os
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.config_loader import config as app_config

class PollinationsProvider(BaseProvider):
    def __init__(self):
        super().__init__("pollinations")
        self.base_url = "https://image.pollinations.ai/prompt/"
        self.proxy = app_config.app_settings.proxy
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        raise NotImplementedError("Pollinations only supports image generation.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        # Pollinations is simple: GET https://image.pollinations.ai/prompt/{prompt}
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Additional params for premium feel
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        seed = kwargs.get("seed", os.urandom(4).hex())
        model = kwargs.get("model", "flux") # Flux is high quality
        
        url = f"{self.base_url}{encoded_prompt}?width={width}&height={height}&seed={seed}&model={model}&nologo=true"
        
        try:
            async with httpx.AsyncClient(timeout=60, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    raise Exception(f"Pollinations Error: {response.status_code}")
                return self.create_result(response.content, "image", model)
        except Exception as e:
            self.log_error("generate_image", e)
            raise e

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Pollinations only supports image and video generation.")

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        # Pollinations improved video triggering
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Use specific animation model flag
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=512&model=flux&seed=123&nologo=true&enhance=true"
        
        try:
            async with httpx.AsyncClient(timeout=60, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                app_logger.info(f"Triggering Pollinations Video for: {prompt}")
                response = await client.get(url)
                if response.status_code != 200:
                    raise Exception(f"Pollinations Video Error: {response.status_code}")
                
                # IMPORTANT: Pollinations image-to-video is still in beta. 
                # If image_bytes is provided, we use a different cinematic rendering path.
                return self.create_result(response.content, "video", "pollinations-flux-video")
        except Exception as e:
            self.log_error("generate_video", e)
            raise e
