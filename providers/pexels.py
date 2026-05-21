import httpx
import os
import asyncio
import random
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config

class PexelsProvider(BaseProvider):
    def __init__(self):
        super().__init__("pexels")
        self.api_key = os.getenv("PEXELS_API_KEY")
        self.base_url = "https://api.pexels.com/videos/search"
        self.proxy = app_config.app_settings.proxy
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        raise NotImplementedError("Pexels only supports video retrieval.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Pexels only supports video retrieval.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Pexels only supports video retrieval.")

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not configured in .env")

        headers = {"Authorization": self.api_key}
        params = {
            "query": prompt,
            "per_page": 5,
            "orientation": "landscape",
            "size": "medium"
        }

        try:
            async with httpx.AsyncClient(timeout=30, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                app_logger.info(f"Searching Pexels for professional video: {prompt}")
                response = await client.get(self.base_url, headers=headers, params=params)
                
                if response.status_code != 200:
                    raise Exception(f"Pexels API Error: {response.status_code}")

                data = response.json()
                videos = data.get("videos", [])

                if not videos:
                    raise Exception(f"No professional videos found for: {prompt}")

                # Pick a random video from the top results for variety
                video_data = random.choice(videos)
                # Get the highest quality HD link
                video_files = video_data.get("video_files", [])
                # Filter for mp4 and reasonable resolution
                best_link = next((f["link"] for f in video_files if f["file_type"] == "video/mp4" and f["width"] >= 1280), video_files[0]["link"])

                app_logger.success(f"Found professional video on Pexels: {best_link}")
                
                # Fetch the actual video bytes
                video_resp = await client.get(best_link)
                return self.create_result(video_resp.content, "video", "pexels-cinematic-v1")

        except Exception as e:
            self.log_error("generate_video", e)
            raise e
