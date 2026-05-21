import os
import asyncio
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from dotenv import load_dotenv

load_dotenv()

class ElevenLabsProvider(BaseProvider):
    def __init__(self):
        super().__init__("elevenlabs")
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
        else:
            self.client = None

        # EXCLUSIVE Female Premium Voice ID (Sia)
        self.locked_voice_id = "6JsmTroalVewG1gA6Jmw"

    async def _get_dynamic_voice_id(self, gender: str) -> str:
        # ABSOLUTE LOCK: Always return the Sia ID provided by user
        return self.locked_voice_id

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        raise NotImplementedError("ElevenLabs only supports audio generation.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("ElevenLabs only supports audio generation.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.client:
            raise ValueError("PRO Voice Engine (ElevenLabs) requires an API Key in your .env file.")

        # ABSOLUTE LOCK: Using the energetic female voice (Sia)
        voice_id = self.locked_voice_id
        
        try:
            app_logger.info(f"ELEVENLABS: Executing with EXCLUSIVE Female VoiceID={voice_id}")
            
            audio_iterator = await asyncio.to_thread(
                self.client.text_to_speech.convert,
                text=prompt,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.6,
                    similarity_boost=0.8,
                    style=0.3,
                    use_speaker_boost=True
                )
            )
            
            audio_bytes = b"".join(list(audio_iterator))
            return self.create_result(audio_bytes, "audio", "elevenlabs-v2-pro")
        except Exception as e:
            self.log_error("generate_audio", e)
            raise e

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("ElevenLabs only supports audio generation.")
