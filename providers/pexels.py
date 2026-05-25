import httpx
import os
import asyncio
import random
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError

class PexelsProvider(BaseProvider):
    def __init__(self):
        super().__init__("pexels")
        self.base_url = "https://api.pexels.com/videos/search"
        self.proxy = app_config.app_settings.proxy
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
        self._configured = False
        self._setup()

    def _setup(self):
        self.api_key = app_config.api_keys.get("PEXELS_API_KEY")
        if self.api_key:
            self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("PEXELS_API_KEY not configured")

        trace_id = kwargs.get("trace_id")
        headers = {"Authorization": self.api_key}
        params = {
            "query": prompt,
            "per_page": 5,
            "orientation": "landscape",
            "size": "medium"
        }

        try:
            async with httpx.AsyncClient(timeout=30, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                app_logger.bind(trace_id=trace_id).info(f"Searching Pexels for professional video: {prompt}")
                response = await client.get(self.base_url, headers=headers, params=params)
                
                if response.status_code != 200:
                    raise ProviderResponseError(f"Pexels API Error: {response.status_code}")

                data = response.json()
                videos = data.get("videos", [])

                if not videos:
                    raise ProviderResponseError(f"No professional videos found for: {prompt}")

                # Pick a random video from the top results for variety
                video_data = random.choice(videos)
                video_files = video_data.get("video_files", [])
                
                # Filter for mp4 and reasonable resolution
                best_link = next((f["link"] for f in video_files if f["file_type"] == "video/mp4" and f["width"] >= 1280), video_files[0]["link"])

                app_logger.bind(trace_id=trace_id).success(f"Found professional video on Pexels: {best_link}")
                
                # Fetch the actual video bytes
                video_resp = await client.get(best_link)
                return self.create_result(video_resp.content, "video", "pexels-cinematic-v1", trace_id=trace_id)

        except Exception as e:
            self.log_error("generate_video", e, trace_id=trace_id)
            raise ProviderError(f"Pexels failed: {str(e)}") from e
