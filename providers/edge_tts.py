import edge_tts
import asyncio
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult

class EdgeTTSProvider(BaseProvider):
    def __init__(self):
        super().__init__("edge-tts")
        # EXCLUSIVE Female English-Indian Voice (Locked for North Indian Tone)
        self.voice = "en-IN-NeerjaNeural"

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        raise NotImplementedError("Edge-TTS only supports audio generation.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Edge-TTS only supports audio generation.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        # ABSOLUTE LOCK: This provider now only speaks in the high-energy female voice
        voice = self.voice

        # MAXIMUM ENERGY TUNING: Strong, Confident, Dynamic
        rate = "+12%"
        volume = "+30%" # Even more projection as requested
        pitch = "+0Hz"

        try:
            from core.logger import app_logger
            app_logger.info(f"Generating EXCLUSIVE FEMALE audio (Voice: {voice})...")
            communicate = edge_tts.Communicate(prompt, voice, rate=rate, pitch=pitch, volume=volume)

            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            
            return self.create_result(audio_bytes, "audio", voice)
        except Exception as e:
            self.log_error("generate_audio", e)
            raise e

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("Edge-TTS only supports audio generation.")
