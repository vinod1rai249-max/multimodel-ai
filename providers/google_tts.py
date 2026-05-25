import os
import asyncio
try:
    from google.cloud import texttospeech
except ImportError:
    import google.cloud.texttospeech as texttospeech
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.config_loader import config as app_config
from core.errors import ProviderNotConfigured, ProviderError, ProviderResponseError

class GoogleTTSProvider(BaseProvider):
    def __init__(self):
        super().__init__("google-cloud-tts")
        self._configured = False
        self.client = None
        # EXCLUSIVE Female Neural2 Voice (Locked)
        self.voice_name = "en-IN-Neural2-A"
        self._setup()

    def _setup(self):
        # Prefer GOOGLE_APPLICATION_CREDENTIALS if set, otherwise try GEMINI_API_KEY
        creds = app_config.api_keys.get("GOOGLE_APPLICATION_CREDENTIALS")
        api_key = app_config.api_keys.get("GEMINI_API_KEY")
        
        try:
            if creds:
                self.client = texttospeech.TextToSpeechAsyncClient()
                self._configured = True
            elif api_key:
                self.client = texttospeech.TextToSpeechAsyncClient(client_options={"api_key": api_key})
                self._configured = True
        except Exception as e:
            app_logger.error(f"Failed to initialize Google TTS: {e}")
            self._configured = False

    def is_configured(self) -> bool:
        return self._configured

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.is_configured():
            raise ProviderNotConfigured("Google Cloud TTS not configured")

        trace_id = kwargs.get("trace_id")
        voice_name = kwargs.get("voice_name", self.voice_name)
        
        input_text = texttospeech.SynthesisInput(text=prompt)
        voice_selection = texttospeech.VoiceSelectionParams(
            language_code="en-IN",
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95,
            pitch=1.2
        )

        try:
            app_logger.bind(trace_id=trace_id).info(f"Generating Google TTS audio ({voice_name})...")
            response = await self.client.synthesize_speech(
                input=input_text, 
                voice=voice_selection, 
                audio_config=audio_config
            )
            return self.create_result(response.audio_content, "audio", voice_name, trace_id=trace_id)
        except Exception as e:
            self.log_error("generate_audio", e, trace_id=trace_id)
            raise ProviderError(f"Google TTS failed: {str(e)}") from e
