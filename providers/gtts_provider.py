import io
import asyncio
from gtts import gTTS
from typing import List, Dict, Any, Optional
from providers.base_provider import BaseProvider
from core.interfaces import GenerationResult
from core.logger import app_logger

class GTTSProvider(BaseProvider):
    def __init__(self):
        super().__init__("google-translate-tts")

    async def generate_text(self, prompt: str, history: List[Dict[str, str]] = [], **kwargs) -> GenerationResult:
        raise NotImplementedError("gTTS only supports audio generation.")

    async def generate_image(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("gTTS only supports audio generation.")

    async def generate_audio(self, prompt: str, **kwargs) -> GenerationResult:
        gender = kwargs.get("voice_gender", "Female")
        
        # gTTS doesn't explicitly support gender, but the India locale 
        # has a very distinct young/dynamic professional North Indian tone.
        # We'll use 'en' with the 'co.in' tld for the authentic accent.
        try:
            app_logger.info(f"Generating free Google Assistant audio (India)...")
            
            # Using tld='co.in' for the North Indian English accent
            tts = await asyncio.to_thread(gTTS, text=prompt, lang='en', tld='co.in', slow=False)
            
            # Save to a buffer
            fp = io.BytesIO()
            await asyncio.to_thread(tts.write_to_fp, fp)
            audio_bytes = fp.getvalue()
            
            return self.create_result(audio_bytes, "audio", "google-assistant-in")
        except Exception as e:
            self.log_error("generate_audio", e)
            raise e

    async def generate_video(self, prompt: str, **kwargs) -> GenerationResult:
        raise NotImplementedError("gTTS only supports audio generation.")
