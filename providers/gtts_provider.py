import io
import asyncio
from gtts import gTTS
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.errors import ProviderError, ProviderResponseError

class GTTSProvider(BaseProvider):
    def __init__(self):
        super().__init__("google-translate-tts")

    def is_configured(self) -> bool:
        return True # Publicly available

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        trace_id = kwargs.get("trace_id")
        
        try:
            app_logger.bind(trace_id=trace_id).info(f"Generating gTTS audio (India)...")
            
            # Using tld='co.in' for the North Indian English accent
            tts = await asyncio.to_thread(gTTS, text=prompt, lang='en', tld='co.in', slow=False)
            
            # Save to a buffer
            fp = io.BytesIO()
            await asyncio.to_thread(tts.write_to_fp, fp)
            audio_bytes = fp.getvalue()
            
            if not audio_bytes:
                raise ProviderResponseError("gTTS returned empty audio")
                
            return self.create_result(audio_bytes, "audio", "google-assistant-in", trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_audio", e, trace_id=trace_id)
            raise ProviderError(f"gTTS failed: {str(e)}") from e
