import os
import asyncio
import httpx
import httpcore
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from dotenv import load_dotenv

load_dotenv()

from core.config_loader import config as app_config

class HuggingFaceProvider(BaseProvider):
    def __init__(self):
        super().__init__("huggingface")
        self.token = os.getenv("HF_TOKEN")
        self.api_url_base = "https://api-inference.huggingface.co/models/"
        self.proxy = app_config.app_settings.proxy
        # Force IPv4 to avoid getaddrinfo errors on some Windows/ISP setups
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

    async def _query(self, model: str, payload: Any) -> bytes:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "MultimodalAIStudio/1.0"
        }
        
        async with httpx.AsyncClient(timeout=150, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
            # If payload is bytes, send as raw data; otherwise send as JSON
            if isinstance(payload, bytes):
                app_logger.info(f"Sending binary payload to HF model: {model}")
                response = await client.post(f"{self.api_url_base}{model}", headers=headers, content=payload)
            else:
                app_logger.info(f"Sending JSON payload to HF model: {model}")
                response = await client.post(f"{self.api_url_base}{model}", headers=headers, json=payload)
            
            if response.status_code == 503:
                # Model is loading
                data = response.json()
                wait_time = data.get("estimated_time", 20)
                app_logger.warning(f"HF Model {model} is loading. Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                # Retry once after loading
                return await self._query(model, payload)
                
            if response.status_code != 200:
                raise Exception(f"HF API Error: {response.status_code} - {response.text}")
            
            return response.content

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        model = kwargs.get("model", "mistralai/Mistral-7B-Instruct-v0.2")
        payload = {"inputs": prompt}
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "MultimodalAIStudio/1.0"
            }
            async with httpx.AsyncClient(timeout=30, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
                response = await client.post(f"{self.api_url_base}{model}", headers=headers, json=payload)
                if response.status_code != 200:
                    raise Exception(f"HF API Error: {response.status_code} - {response.text}")
                data = response.json()
                return self.create_result(data[0]['generated_text'], "text", model)
        except Exception as e:
            self.log_error("generate_text", e)
            raise e

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        model = kwargs.get("model", "stabilityai/stable-diffusion-xl-base-1.0")
        try:
            # Standard SDXL payload
            image_bytes = await self._query(model, {"inputs": prompt})
            return self.create_result(image_bytes, "image", model)
        except Exception as e:
            self.log_error("generate_image", e)
            raise e

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        model = kwargs.get("model", "facebook/musicgen-small")
        try:
            # MusicGen expects JSON
            audio_bytes = await self._query(model, {"inputs": prompt})
            return self.create_result(audio_bytes, "audio", model)
        except Exception as e:
            self.log_error("generate_audio", e)
            raise e

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        # Determine model based on style and input
        video_style = kwargs.get("video_style", "Natural")
        
        if image_bytes:
            # Image-to-Video (Professional Animation)
            model = "stabilityai/stable-video-diffusion-img2vid-xt"
            # SVD via Inference API expects the raw binary image as the request body
            payload = image_bytes 
        else:
            # Text-to-Video
            if video_style == "Animation":
                model = "guoyww/AnimateDiff"
            else:
                model = "ali-vilab/text-to-video-ms-1.7b"
            payload = {"inputs": prompt}

        try:
            # SVD and other heavy models need longer timeouts
            video_data = await self._query(model, payload)
            return self.create_result(video_data, "video", model)
        except Exception as e:
            self.log_error("generate_video", e)
            # If it's a connection error, let's be explicit for the orchestrator
            raise e
