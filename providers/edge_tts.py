import edge_tts
import asyncio
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.errors import ProviderError, ProviderResponseError

class EdgeTTSProvider(BaseProvider):
    def __init__(self):
        super().__init__("edge-tts")
        # EXCLUSIVE Female English-Indian Voice (Locked for North Indian Tone)
        self.voice = "en-IN-NeerjaNeural"

    def is_configured(self) -> bool:
        return True # Publicly available

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        trace_id = kwargs.get("trace_id")
        voice = kwargs.get("voice", self.voice)
        
        # MAXIMUM ENERGY TUNING: Strong, Confident, Dynamic
        rate = kwargs.get("rate", "+12%")
        volume = kwargs.get("volume", "+30%")
        pitch = kwargs.get("pitch", "+0Hz")

        try:
            app_logger.bind(trace_id=trace_id).info(f"Generating Edge-TTS audio (Voice: {voice})...")
            communicate = edge_tts.Communicate(prompt, voice, rate=rate, pitch=pitch, volume=volume)

            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            
            if not audio_bytes:
                raise ProviderResponseError("Edge-TTS returned empty audio")
                
            return self.create_result(audio_bytes, "audio", voice, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_audio", e, trace_id=trace_id)
            raise ProviderError(f"Edge-TTS failed: {str(e)}") from e
