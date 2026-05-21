import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from dotenv import load_dotenv

load_dotenv()

from core.config_loader import config as app_config

class OpenRouterProvider(BaseProvider):
    def __init__(self):
        super().__init__("openrouter")
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.proxy = app_config.app_settings.proxy
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
            
        model = kwargs.pop("model", "anthropic/claude-3-haiku")
        return await self._process_request(prompt, model, "text", **kwargs)

    async def _process_request(self, prompt: str, model: str, content_type: str, **kwargs) -> GenerationResult:
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
                if response.status_code != 200:
                    raise Exception(f"OpenRouter Error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                if content_type == "image":
                    # OpenRouter returns image URL in message content or as a separate field
                    content = data['choices'][0]['message']['content']
                else:
                    content = data['choices'][0]['message']['content']
                
                # If the response is meant to be a file (URL), handle it
                if content_type in ["image", "audio"]:
                    if content.startswith("http"):
                        media_resp = await client.get(content)
                        return self.create_result(media_resp.content, content_type, model)
                
                return self.create_result(content, content_type, model)
        except Exception as e:
            self.log_error(f"generate_{content_type}", e)
            raise e

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        # Use Flux Schnell on OpenRouter for reliable, high-quality images
        model = kwargs.pop("model", "black-forest-labs/flux-1-schnell")
        return await self._process_request(prompt, model, "image", **kwargs)

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        # OpenRouter supports OpenAI TTS models
        model = kwargs.pop("model", "openai/tts-1")
        return await self._process_request(prompt, model, "audio", **kwargs)

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("OpenRouter does not support video generation yet.")
