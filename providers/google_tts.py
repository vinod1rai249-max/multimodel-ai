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

class GoogleTTSProvider(BaseProvider):
    def __init__(self):
        super().__init__("google-cloud-tts")
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                self.client = texttospeech.TextToSpeechAsyncClient(client_options={"api_key": self.api_key})
            except Exception:
                self.client = None
        else:
            self.client = None

        # EXCLUSIVE Female Neural2 Voice (Locked)
        self.voice_name = "en-IN-Neural2-A"

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        raise NotImplementedError("GoogleTTS only supports audio generation.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("GoogleTTS only supports audio generation.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        if not self.client:
            raise ValueError("Google Cloud TTS client not initialized. Ensure GEMINI_API_KEY is valid.")

        # ABSOLUTE LOCK: Using the energetic female voice
        voice_name = self.voice_name
        
        # Audio Configuration for "Premium, energetic, crisp and clear"
        input_text = texttospeech.SynthesisInput(text=prompt)
        
        voice_selection = texttospeech.VoiceSelectionParams(
            language_code="en-IN",
            name=voice_name
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95, # Energetic pace
            pitch=1.2 # Youthful boost
        )

        try:
            app_logger.info(f"Generating EXCLUSIVE premium female audio ({voice_name})...")
            response = await self.client.synthesize_speech(
                input=input_text, 
                voice=voice_selection, 
                audio_config=audio_config
            )
            return self.create_result(response.audio_content, "audio", voice_name)
        except Exception as e:
            self.log_error("generate_audio", e)
            raise e

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("GoogleTTS only supports audio generation.")
