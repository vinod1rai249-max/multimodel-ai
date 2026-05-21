import os
import hashlib
import aiofiles
from core.logger import app_logger

class MediaCache:
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _generate_key(self, prompt: str, provider: str, content_type: str, model: str = "", metadata: dict = {}) -> str:
        # Include model in key to ensure that switching to a new voice model (e.g. Wavenet -> Neural2)
        # forces the app to generate a fresh file.
        unique_str = f"{prompt}_{provider}_{model}_{content_type}_{str(metadata)}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    async def save_media(self, prompt: str, provider: str, content_type: str, data: bytes, extension: str, model: str = "", metadata: dict = {}) -> str:
        key = self._generate_key(prompt, provider, content_type, model, metadata)
        file_name = f"{key}.{extension}"
        file_path = os.path.join(self.cache_dir, file_name)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)
        
        app_logger.debug(f"Saved {content_type} to cache: {file_path}")
        return file_path

    def get_media_path(self, prompt: str, provider: str, content_type: str, extension: str, model: str = "", metadata: dict = {}) -> str:
        key = self._generate_key(prompt, provider, content_type, model, metadata)
        file_name = f"{key}.{extension}"
        file_path = os.path.join(self.cache_dir, file_name)
        return file_path if os.path.exists(file_path) else None

# Singleton instance
cache = MediaCache()
