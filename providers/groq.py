from core.logger import app_logger
from groq import Groq
import os
import asyncio
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from dotenv import load_dotenv

load_dotenv()

import httpx

class GroqProvider(BaseProvider):
    def __init__(self):
        super().__init__("groq")
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            # Force IPv4 via custom httpx client for Groq SDK
            http_client = httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))
            self.client = Groq(api_key=api_key, http_client=http_client)
        else:
            self.client = None

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.client:
            raise ValueError("Groq API key not configured")
        
        # Use kwargs.pop to ensure 'model' isn't passed twice downstream
        model = kwargs.pop("model", "llama-3.3-70b-versatile")
        
        try:
            return await self._execute_request(prompt, model, **kwargs)
        except Exception as e:
            # Check if decommissioning error
            error_str = str(e).lower()
            if "decommissioned" in error_str or "not found" in error_str or "400" in error_str:
                app_logger.warning(f"Groq model {model} failed. Attempting dynamic discovery...")
                try:
                    models = await asyncio.to_thread(self.client.models.list)
                    # Pick the first available versatile llama model as a backup
                    backup_model = next((m.id for m in models.data if "llama" in m.id.lower() and "versatile" in m.id.lower()), models.data[0].id)
                    app_logger.info(f"Falling back to discovered Groq model: {backup_model}")
                    return await self._execute_request(prompt, backup_model, **kwargs)
                except Exception as inner_e:
                    app_logger.error(f"Groq dynamic discovery failed: {str(inner_e)}")
            
            self.log_error("generate_text", e)
            raise e

    async def _execute_request(self, prompt: str, model_id: str, **kwargs) -> GenerationResult:
        messages = [{"role": "user", "content": prompt}]
        completion = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=model_id,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        )
        return self.create_result(completion.choices[0].message.content, "text", model_id)

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Groq does not support image generation.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Groq does not support audio generation.")

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Groq does not support video generation.")

    async def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> str:
        if not self.client:
            raise ValueError("Groq API key not configured")
        
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        try:
            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.log_error("analyze_image", e)
            raise e
