import asyncio
from typing import List, Dict, Any, Optional
from core.config_loader import config, ModelConfig
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.cache import cache
from providers.gemini import GeminiProvider
from providers.groq import GroqProvider
from providers.huggingface import HuggingFaceProvider
from providers.openrouter import OpenRouterProvider
from providers.edge_tts import EdgeTTSProvider
from providers.google_tts import GoogleTTSProvider
from providers.gtts_provider import GTTSProvider
from providers.elevenlabs import ElevenLabsProvider
from providers.pollinations import PollinationsProvider
from providers.pexels import PexelsProvider

class AsyncOrchestrator:
    def __init__(self):
        self.providers = {
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "huggingface": HuggingFaceProvider(),
            "openrouter": OpenRouterProvider(),
            "edge-tts": EdgeTTSProvider(),
            "google-cloud-tts": GoogleTTSProvider(),
            "google-translate-tts": GTTSProvider(),
            "elevenlabs": ElevenLabsProvider(),
            "pollinations": PollinationsProvider(),
            "pexels": PexelsProvider(),
        }

    async def _execute_with_fallback(self, chain: List[ModelConfig], method_name: str, prompt: str, **kwargs) -> GenerationResult:
        last_error = None
        
        app_logger.info(f"🌀 [ROUTING] Starting execution chain for '{method_name}'...")
        
        for i, model_cfg in enumerate(chain):
            provider_instance = self.providers.get(model_cfg.provider)
            if not provider_instance:
                app_logger.warning(f"⚠️ [ROUTING] Attempt {i+1}: Provider {model_cfg.provider} not found.")
                continue
            
            app_logger.info(f"➡️ [ATTEMPT {i+1}] Provider: {model_cfg.provider} | Model: {model_cfg.model}")
            
            try:
                method = getattr(provider_instance, method_name)
                # Merge model specific config from yaml into kwargs
                merged_kwargs = {**kwargs, "model": model_cfg.model}
                
                # Execute with timeout
                result = await asyncio.wait_for(method(prompt, **merged_kwargs), timeout=model_cfg.timeout)
                app_logger.success(f"✅ [SUCCESS] Request fulfilled by {model_cfg.provider} ({model_cfg.model}).")
                return result
            except (asyncio.TimeoutError, Exception) as e:
                app_logger.warning(f"⚠️ [FAILED] Attempt {i+1} ({model_cfg.provider}) failed: {str(e)[:100]}...")
                last_error = e
                continue
        
        app_logger.critical(f"🚫 [CHAIN EXHAUSTED] All {len(chain)} providers failed for '{method_name}'.")
        raise last_error or Exception(f"No providers available for {method_name}")

    async def generate(self, prompt: str, output_type: str = "text", image_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        # 1. SMART VISION BRIDGE: If image is uploaded for a video, describe it first to improve search
        if image_bytes and output_type == "video":
            app_logger.info("Image detected for video generation. Triggering Smart Vision Bridge...")
            try:
                # Use Groq Vision to describe the image
                vision_provider = self.providers.get("groq")
                image_description = await vision_provider.analyze_image(
                    image_bytes, 
                    "Describe this image in 5-8 words for a stock video search. focus on the main subject and action."
                )
                app_logger.info(f"Vision Bridge Description: {image_description}")
                # Combine user prompt with vision description for a 'converted' feel
                prompt = f"{image_description} {prompt}"
            except Exception as e:
                app_logger.warning(f"Vision Bridge failed: {str(e)}. Continuing with original prompt.")

        # Define Expert Personas based on output type
        personas = {
            "text": "SYSTEM INSTRUCTION: You are an Elite AI Research Scientist. Your responses are professional, insightful, and structured.",
            "image": "SYSTEM INSTRUCTION: You are a World-Class Digital Artist. Describe visual textures, lighting, and composition with artistic precision.",
            "audio": "SYSTEM INSTRUCTION: You are a Premium Voice Artist and Sound Engineer. Describe the tone, pace, and sonic environment of an audio clip.",
            "video": "SYSTEM INSTRUCTION: You are a Master Cinematographer. Describe camera lenses, motion, lighting, and cinematic transitions vividly."
        }
        
        persona = personas.get(output_type, personas["text"])

        if output_type == "text":
            chain = config.routing.text_generation
            method = "generate_text"
            prompt = f"{persona}\n\nUser Prompt: {prompt}"
        elif output_type == "image":
            chain = config.routing.image_generation
            method = "generate_image"
        elif output_type == "audio":
            # 100% FREE AUDIO ENGINE: Using Edge-TTS as the primary provider
            app_logger.info("Free Audio Engine requested. Routing to system defaults...")
            chain = config.routing.audio_generation
            method = "generate_audio"
        elif output_type == "video":
            chain = config.routing.video_generation
            method = "generate_video"
        else:
            raise ValueError(f"Unsupported output type: {output_type}")

        try:
            # Special handling for video which can take image_bytes
            if output_type == "video":
                result = await self._execute_with_fallback(chain, method, prompt, image_bytes=image_bytes, **kwargs)
            else:
                result = await self._execute_with_fallback(chain, method, prompt, **kwargs)
        except Exception as e:
            app_logger.error(f"All media providers failed for {output_type}: {str(e)}. Falling back to text description.")
            # Graceful Degradation: ABSOLUTE STRICT SYSTEM PROMPT
            fallback_prompt = (
                f"{persona}\n\n"
                f"CRITICAL SYSTEM INSTRUCTION: YOU ARE A CINEMATIC SCREENWRITER. DO NOT CHAT. DO NOT ADVISE.\n"
                f"The user requested a {output_type} with this prompt: \"{prompt}\".\n"
                "The server is currently busy. Your ONLY job is to write a VIVID, SENSORY DESCRIPTION of the scene.\n"
                "RULES:\n"
                "- DO NOT give steps or instructions.\n"
                "- DO NOT mention software like Adobe, Lumen5, or Premiere.\n"
                "- DO NOT say 'Here is a guide' or 'Method 1'.\n"
                f"- JUST START DESCRIBING THE {output_type.upper()} CONTENT ITSELF (Lighting, motion, textures).\n"
                f"- Start with ' [SCENE VISUALIZATION]: '"
            )
            result = await self._execute_with_fallback(config.routing.text_generation, "generate_text", fallback_prompt, **kwargs)
            return result
        
        # Post-processing: Save media to cache if it's not text
        if result.content_type != "text":
            # Ensure the result content type matches the requested output type
            # This prevents a 'text description' or 'audio' from being mislabeled
            if result.content_type != output_type and output_type != "text":
                app_logger.warning(f"Result type mismatch: Got {result.content_type}, requested {output_type}. Adjusting labels.")
            
            ext_map = {"image": "png", "audio": "wav", "video": "mp4"}
            extension = ext_map.get(output_type, "bin")
            
            # CRITICAL FIX: Pass result.model to save_media. This ensures that 
            # changing the voice model in code (e.g. Wavenet -> Neural2)
            # results in a unique filename so the browser/user hears the update.
            file_path = await cache.save_media(
                prompt, 
                result.provider, 
                output_type, 
                result.content, 
                extension, 
                model=result.model, 
                metadata=kwargs
            )
            result.content = file_path 
            result.content_type = output_type # Force correct rendering in Streamlit
            
        return result

# Singleton instance
orchestrator = AsyncOrchestrator()
