import replicate
import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError, ProviderAuthError

class ReplicateProvider(BaseProvider):
    def __init__(self):
        super().__init__("replicate")
        self._configured = False
        self._setup()

    def _setup(self):
        self.api_token = app_config.api_keys.get("REPLICATE_API_TOKEN")
        if self.api_token:
            os.environ["REPLICATE_API_TOKEN"] = self.api_token

    def is_configured(self) -> bool:
        if not self.api_token:
            return False
            
        # For video specifically, we need a valid model reference
        model = app_config.app_settings.replicate_image_to_video_model
        if not model or ":" not in model:
            return False
            
        # Reject specific invalid values
        if model.lower() in ["kling-v3-video", "stability-ai/stable-video-diffusion", "placeholder", "your_model_here"]:
            return False
            
        return True

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        if not self.is_configured():
            model = app_config.app_settings.replicate_image_to_video_model
            if model and ":" not in model:
                 raise ProviderNotConfigured("Invalid Replicate model reference. Expected owner/name:version.")
            raise ProviderNotConfigured("REPLICATE_API_TOKEN or valid REPLICATE_IMAGE_TO_VIDEO_MODEL not configured")
        
        # Use model from kwargs (which comes from centralized routing config)
        model_name = kwargs.get("model", app_config.app_settings.replicate_image_to_video_model)
        trace_id = kwargs.get("trace_id")

        # VALIDATION: Reject Kling models in Replicate provider
        if "kling" in model_name.lower():
             raise ProviderError(f"Replicate provider cannot handle Kling models: {model_name}")

        # VALIDATION: Check model format owner/name:version
        if ":" not in model_name or "/" not in model_name:
             raise ProviderError(f"Invalid Replicate model format: {model_name}. Expected 'owner/name:version'.")
        
        try:
            # Replicate SVD or AnimateDiff usually takes an image or prompt
            input_data = {"prompt": prompt}
            
            if image_bytes:
                # For models like SVD, we might need to upload the image or pass it as bytes
                # Replicate's python client handles file-like objects
                import io
                input_data["image"] = io.BytesIO(image_bytes)
            
            app_logger.bind(trace_id=trace_id).info(f"Replicate: Running model {model_name}...")
            
            # Run the model (Replicate client is synchronous, so we run in thread)
            # Some models use different input keys, lucataco/animate-diff uses 'motion_module' etc.
            # but usually 'prompt' is common.
            # For stability-ai/stable-video-diffusion, it uses 'input_image'.
            
            if "stable-video-diffusion" in model_name:
                input_data = {"input_image": io.BytesIO(image_bytes)} if image_bytes else {"prompt": prompt}

            output = await asyncio.to_thread(replicate.run, model_name, input=input_data)
            
            if not output:
                raise ProviderResponseError("Replicate returned no output")
            
            # Output is typically a URL or list of URLs
            video_url = output[0] if isinstance(output, list) else output
            
            if not str(video_url).startswith("http"):
                raise ProviderResponseError(f"Replicate returned invalid video URL: {video_url}")

            app_logger.bind(trace_id=trace_id).info(f"Replicate: Video generated at {video_url}")
            
            # Download the video
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(str(video_url))
                if resp.status_code != 200:
                    raise ProviderResponseError(f"Failed to download video from Replicate: {resp.status_code}")
                video_bytes = resp.content

            result = self.create_result(video_bytes, "video", model_name, trace_id=trace_id)
            result.metadata["real_video"] = True
            result.metadata["response_type"] = "video"
            return result
            
        except Exception as e:
            self.log_error("generate_video", e, trace_id=trace_id)
            if "401" in str(e):
                raise ProviderAuthError(f"Replicate Authentication failed: {str(e)}")
            raise ProviderError(f"Replicate video generation failed: {str(e)}") from e

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("REPLICATE_API_TOKEN not configured")
        
        model_name = kwargs.get("model", "stability-ai/sdxl")
        trace_id = kwargs.get("trace_id")
        
        try:
            output = await asyncio.to_thread(replicate.run, model_name, input={"prompt": prompt})
            image_url = output[0] if isinstance(output, list) else output
            
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(str(image_url))
                return self.create_result(resp.content, "image", model_name, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_image", e, trace_id=trace_id)
            raise ProviderError(f"Replicate image generation failed: {str(e)}") from e
