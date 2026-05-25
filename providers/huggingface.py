import os
import asyncio
import httpx
import httpcore
import socket
from typing import List, Dict, Any, Optional, Union
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError, ProviderAuthError, NetworkDNSError

class HuggingFaceProvider(BaseProvider):
    def __init__(self):
        super().__init__("huggingface")
        self.api_url_base = "https://api-inference.huggingface.co/models/"
        self.proxy = app_config.app_settings.proxy
        # Force IPv4 to avoid getaddrinfo errors on some Windows/ISP setups
        self.transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
        self._configured = False
        self._setup()

    def _setup(self):
        self.token = app_config.api_keys.get("HF_TOKEN")
        if self.token:
            self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    async def _query(self, model: str, payload: Any, trace_id: str = None) -> bytes:
        if not self.is_configured():
            raise ProviderNotConfigured("HF_TOKEN not configured")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "MultimodalAIStudio/1.0"
        }
        
        async with httpx.AsyncClient(timeout=150, proxy=self.proxy, trust_env=True, transport=self.transport) as client:
            try:
                # If payload is bytes, send as raw data; otherwise send as JSON
                if isinstance(payload, bytes):
                    response = await client.post(f"{self.api_url_base}{model}", headers=headers, content=payload)
                else:
                    response = await client.post(f"{self.api_url_base}{model}", headers=headers, json=payload)
                
                if response.status_code == 503:
                    # Model is loading
                    data = response.json()
                    wait_time = data.get("estimated_time", 20)
                    app_logger.bind(trace_id=trace_id).warning(f"HF Model {model} is loading. Waiting {wait_time}s...")
                    await asyncio.sleep(min(wait_time, 30)) # Don't wait forever
                    # Retry once after loading
                    return await self._query(model, payload, trace_id=trace_id)
                    
                if response.status_code == 401:
                    raise ProviderAuthError(f"HF Authentication failed: {response.text}")
                elif response.status_code == 403:
                    raise ProviderAuthError(f"HF Access Denied (403): {response.text}")
                elif response.status_code == 429:
                    raise ProviderResponseError(f"HF Rate Limited (429): {response.text}")
                elif response.status_code != 200:
                    raise ProviderResponseError(f"HF API Error: {response.status_code} - {response.text}")
                
                return response.content
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError, socket.gaierror) as e:
                err_msg = str(e)
                app_logger.bind(trace_id=trace_id).error(f"HF Network/DNS Error: {err_msg}")
                raise NetworkDNSError(f"HuggingFace network/DNS unreachable: {err_msg}. Please check your internet connection, VPN, or firewall.")
            except (ProviderAuthError, ProviderResponseError):
                raise
            except Exception as e:
                raise ProviderError(f"HF Query failed: {str(e)}") from e

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("HF_TOKEN not configured")
        
        model = kwargs.get("model", "mistralai/Mistral-7B-Instruct-v0.2")
        trace_id = kwargs.pop("trace_id", None)
        payload = {"inputs": prompt}
        try:
            content = await self._query(model, payload, trace_id=trace_id)
            # HF text models return JSON bytes
            import json
            data = json.loads(content)
            if isinstance(data, list) and len(data) > 0 and 'generated_text' in data[0]:
                return self.create_result(data[0]['generated_text'], "text", model, trace_id=trace_id)
            elif isinstance(data, dict) and 'generated_text' in data:
                 return self.create_result(data['generated_text'], "text", model, trace_id=trace_id)
            raise ProviderResponseError(f"HF Text generation unexpected response: {data}")
        except Exception as e:
            self.log_error("generate_text", e, trace_id=trace_id)
            raise e

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("HF_TOKEN not configured")
        model = kwargs.get("model", "stabilityai/stable-diffusion-xl-base-1.0")
        trace_id = kwargs.pop("trace_id", None)
        try:
            image_bytes = await self._query(model, {"inputs": prompt}, trace_id=trace_id)
            return self.create_result(image_bytes, "image", model, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_image", e, trace_id=trace_id)
            raise e

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("HF_TOKEN not configured")
        model = kwargs.get("model", "facebook/musicgen-small")
        trace_id = kwargs.pop("trace_id", None)
        try:
            audio_bytes = await self._query(model, {"inputs": prompt}, trace_id=trace_id)
            return self.create_result(audio_bytes, "audio", model, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_audio", e, trace_id=trace_id)
            raise e

    async def generate_video(self, prompt: str, image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("HF_TOKEN not configured")
        
        trace_id = kwargs.pop("trace_id", None)
        video_style = kwargs.get("video_style", "Natural")
        
        if image_bytes:
            model = "stabilityai/stable-video-diffusion-img2vid-xt"
            payload = image_bytes 
        else:
            if video_style == "Animation":
                model = "guoyww/AnimateDiff"
            else:
                model = "ali-vilab/text-to-video-ms-1.7b"
            payload = {"inputs": prompt}

        try:
            video_data = await self._query(model, payload, trace_id=trace_id)
            return self.create_result(video_data, "video", model, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_video", e, trace_id=trace_id)
            raise e

    async def analyze_image(self, image_data: Union[bytes, List[bytes]], prompt: str, **kwargs) -> str:
        if not self.is_configured():
            raise ProviderNotConfigured("HF_TOKEN not configured")
        
        # HF Inference API for vision usually takes raw bytes of ONE image
        if isinstance(image_data, list):
             # For HF, we take the first frame for now as most inference models take one
             image_bytes = image_data[0] if image_data else b""
        else:
             image_bytes = image_data

        model = kwargs.get("model", app_config.app_settings.hf_vision_model)
        trace_id = kwargs.pop("trace_id", None)
        try:
            content = await self._query(model, image_bytes, trace_id=trace_id)
            import json
            data = json.loads(content)
            if isinstance(data, list) and len(data) > 0 and 'generated_text' in data[0]:
                return data[0]['generated_text']
            return str(data)
        except Exception as e:
            # Check for network/DNS errors specifically
            err_msg = str(e)
            if "getaddrinfo failed" in err_msg or "ConnectError" in err_msg:
                app_logger.bind(trace_id=trace_id).error(f"HF Vision Network/DNS Error: {err_msg}")
                raise NetworkDNSError(f"HuggingFace network/DNS unreachable: {err_msg}")
            
            self.log_error("analyze_image", e, trace_id=trace_id)
            raise e
