import os
import asyncio
import httpx
import base64
import time
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import (
    ProviderNotConfigured, ProviderError, ProviderResponseError, 
    ProviderAuthError, ProviderCreditError, ProviderTimeoutError,
    ProviderModerationError, NetworkDNSError
)

class KlingProvider(BaseProvider):
    def __init__(self):
        super().__init__("kling")
        # Note: Kling AI API typically requires specific headers and payload formats.
        # This implementation follows the standard polling pattern.
        self.api_url = "https://api.klingai.com/v1" 
        self._configured = False
        self._setup()

    def _setup(self):
        self.api_key = app_config.api_keys.get("KLING_API_KEY")
        if self.api_key and self.api_key.lower() not in ["placeholder", "your_kling_key"]:
            self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("KLING_API_KEY not configured")
        
        trace_id = kwargs.get("trace_id")
        model_name = kwargs.get("model", app_config.app_settings.kling_image_to_video_model)
        timeout = kwargs.get("timeout", 120)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Step 1: Submit Job
            payload = {
                "model": model_name,
                "prompt": prompt,
                "config": {
                    "aspect_ratio": "16:9"
                }
            }
            
            if image_bytes:
                b64_image = base64.b64encode(image_bytes).decode('utf-8')
                payload["image"] = f"data:image/jpeg;base64,{b64_image}"
                payload["type"] = "image_to_video"
            else:
                payload["type"] = "text_to_video"

            app_logger.bind(trace_id=trace_id).info(f"Kling: Submitting job for model {model_name}...")
            
            async with httpx.AsyncClient(timeout=30) as client:
                # This is a representative API structure for Kling
                response = await client.post(f"{self.api_url}/videos/generations", headers=headers, json=payload)
                
                if response.status_code == 401:
                    raise ProviderAuthError("Kling: Authentication failed (Invalid API Key)")
                elif response.status_code == 402:
                    raise ProviderCreditError("Kling: Insufficient credits")
                elif response.status_code != 200:
                    raise ProviderResponseError(f"Kling API Error: {response.status_code} - {response.text}")
                
                data = response.json()
                job_id = data.get("data", {}).get("task_id") or data.get("id")
                if not job_id:
                    raise ProviderResponseError(f"Kling: No task ID returned: {data}")

                # Step 2: Poll for completion
                app_logger.bind(trace_id=trace_id).info(f"Kling: Job {job_id} submitted. Polling (max {timeout}s)...")
                
                start_time = time.time()
                while time.time() - start_time < timeout:
                    poll_resp = await client.get(f"{self.api_url}/videos/generations/{job_id}", headers=headers)
                    if poll_resp.status_code != 200:
                        app_logger.bind(trace_id=trace_id).warning(f"Kling: Polling failed with {poll_resp.status_code}")
                        await asyncio.sleep(5)
                        continue
                    
                    job_data = poll_resp.json()
                    # Standard Kling task data structure
                    task_info = job_data.get("data", {})
                    status = task_info.get("task_status", "").lower() or job_data.get("status", "").lower()
                    
                    if status in ["succeed", "completed", "success"]:
                        video_url = task_info.get("video_url") or task_info.get("url")
                        if not video_url:
                             raise ProviderResponseError(f"Kling: Task succeeded but no URL found: {job_data}")
                        
                        app_logger.bind(trace_id=trace_id).info(f"Kling: Video ready at {video_url}")
                        
                        # Download video
                        video_resp = await client.get(video_url)
                        if video_resp.status_code != 200:
                            raise ProviderResponseError(f"Kling: Failed to download video file: {video_resp.status_code}")
                        
                        result = self.create_result(video_resp.content, "video", model_name, trace_id=trace_id)
                        result.metadata["real_video"] = True
                        result.metadata["response_type"] = "video"
                        return result
                    
                    elif status in ["failed", "error"]:
                        reason = task_info.get("task_status_msg") or "Unknown error"
                        raise ProviderResponseError(f"Kling: Generation failed - {reason}")
                    
                    elif status == "rejected":
                        raise ProviderModerationError("Kling: Content rejected by safety filters")
                    
                    await asyncio.sleep(5)
                
                raise ProviderTimeoutError(f"Kling: Job {job_id} timed out after {timeout}s")

        except (httpx.NetworkError, httpx.ConnectError) as e:
            raise NetworkDNSError(f"Kling: Network unreachable or DNS failure - {str(e)}")
        except Exception as e:
            if isinstance(e, (ProviderAuthError, ProviderCreditError, ProviderTimeoutError, ProviderResponseError, ProviderNotConfigured, ProviderModerationError, NetworkDNSError)):
                raise
            self.log_error("generate_video", e, trace_id=trace_id)
            raise ProviderError(f"Kling: Unexpected failure - {str(e)}") from e
