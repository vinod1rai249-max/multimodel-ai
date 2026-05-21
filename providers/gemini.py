import warnings
# Suppress the deprecation warning for google-generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai
import os
import asyncio
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from dotenv import load_dotenv

load_dotenv()

from core.logger import app_logger
from core.config_loader import config as app_config

class GeminiProvider(BaseProvider):
    def __init__(self):
        super().__init__("gemini")
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model_name = "models/gemini-1.5-flash"
        else:
            self.model_name = None

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.model_name:
            raise ValueError("Gemini API key not configured")
        
        # Ensure 'model' is removed from kwargs before passing to helper
        model_id = kwargs.pop("model", self.model_name)
        if "models/" not in model_id:
            model_id = f"models/{model_id}"
        
        try:
            return await self._execute_request(prompt, model_id, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "not found" in error_str or "404" in error_str or "not supported" in error_str:
                app_logger.warning(f"Gemini model {model_id} failed. Attempting dynamic discovery...")
                try:
                    # Query available models
                    models = await asyncio.to_thread(genai.list_models)
                    # Filter for models that support generate_content and are stable 1.5/2.0 variants
                    # Avoid preview and experimental models
                    stable_models = [
                        m.name for m in models 
                        if "generateContent" in m.supported_generation_methods 
                        and ("1.5" in m.name or "2.0" in m.name)
                        and "preview" not in m.name.lower()
                        and "exp" not in m.name.lower()
                    ]
                    
                    if stable_models:
                        backup_model = stable_models[0]
                        app_logger.info(f"Falling back to discovered Gemini model: {backup_model}")
                        return await self._execute_request(prompt, backup_model, **kwargs)
                except Exception as inner_e:
                    app_logger.error(f"Gemini dynamic discovery failed: {str(inner_e)}")

            self.log_error("generate_text", e)
            raise e

    async def _execute_request(self, prompt: str, model_name: str, **kwargs) -> GenerationResult:
        model = genai.GenerativeModel(model_name)
        response = await model.generate_content_async(
            prompt,
            generation_config={
                "temperature": kwargs.get("temperature", 0.7),
                "max_output_tokens": kwargs.get("max_tokens", 2048),
            }
        )
        return self.create_result(response.text, "text", model_name)

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Gemini does not support image generation in this version.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Gemini does not support audio generation.")

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Gemini does not support video generation.")
