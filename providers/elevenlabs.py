import os
import asyncio
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError

class ElevenLabsProvider(BaseProvider):
    def __init__(self):
        super().__init__("elevenlabs")
        self._configured = False
        self.client = None
        # EXCLUSIVE Female Premium Voice ID (Sia)
        self.locked_voice_id = "6JsmTroalVewG1gA6Jmw"
        self._setup()

    def _setup(self):
        self.api_key = app_config.api_keys.get("ELEVENLABS_API_KEY")
        if self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
            self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("ElevenLabs API Key not configured")

        trace_id = kwargs.get("trace_id")
        voice_id = kwargs.get("voice_id", self.locked_voice_id)
        
        try:
            app_logger.bind(trace_id=trace_id).info(f"ELEVENLABS: Executing with VoiceID={voice_id}")
            
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
            if not audio_bytes:
                raise ProviderResponseError("ElevenLabs returned empty audio")
            return self.create_result(audio_bytes, "audio", "elevenlabs-v2-pro", trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_audio", e, trace_id=trace_id)
            raise ProviderError(f"ElevenLabs failed: {str(e)}") from e
