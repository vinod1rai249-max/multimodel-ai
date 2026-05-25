import asyncio
import uuid
import time
import os
from typing import List, Dict, Any, Optional, Union
from core.config_loader import config, ModelConfig
from core.interfaces import GenerationResult
from core.logger import app_logger
from core.cache import cache
from utils.video_frames import extract_key_frames
from core.errors import (
    ProviderNotConfigured, ProviderError, ProviderAuthError, 
    ProviderRateLimitError, ProviderTimeoutError, ProviderResponseError,
    UnsupportedRouteError, AllProvidersFailedError
)
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
from providers.replicate import ReplicateProvider
from providers.kling import KlingProvider

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
            "replicate": ReplicateProvider(),
        }
        
        # Conditional registration for Kling
        kling_key = config.api_keys.get("KLING_API_KEY")
        img2vid_provider = config.app_settings.image_to_video_provider
        kling_model = config.app_settings.kling_image_to_video_model
        
        if kling_key and img2vid_provider == "kling":
            self.providers["kling"] = KlingProvider()
            app_logger.info(f"Kling registered successfully with model {kling_model}")
        elif not kling_key:
            app_logger.info("Kling skipped: KLING_API_KEY not configured")

    async def _execute_with_fallback(self, chain_configs: List[ModelConfig], method_name: str, prompt: str, trace_id: str, **kwargs) -> GenerationResult:
        failed_providers = []
        
        app_logger.bind(trace_id=trace_id).info(f"🌀 [ROUTING] Starting fallback chain for '{method_name}'...")
        
        for i, model_cfg in enumerate(chain_configs):
            provider_instance = self.providers.get(model_cfg.provider)
            if not provider_instance:
                app_logger.bind(trace_id=trace_id).warning(f"⚠️ [ROUTING] Attempt {i+1}: Provider {model_cfg.provider} not found in registry.")
                continue
            
            if not provider_instance.is_configured():
                reason = f"Provider {model_cfg.provider} is not configured (missing API key)."
                app_logger.bind(trace_id=trace_id).warning(f"⚠️ [ROUTING] Attempt {i+1}: {reason}")
                failed_providers.append({
                    "provider": model_cfg.provider,
                    "model": model_cfg.model,
                    "error": "NotConfigured",
                    "message": reason
                })
                continue

            app_logger.bind(trace_id=trace_id).info(f"➡️ [ATTEMPT {i+1}] Provider: {model_cfg.provider} | Model: {model_cfg.model}")
            
            try:
                method = getattr(provider_instance, method_name)
                
                # Defensive Cleanup: Ensure trace_id and route aren't duplicated in kwargs
                # This prevents 'got multiple values for keyword argument' errors
                kwargs.pop("trace_id", None)
                kwargs.pop("route", None)
                
                # Merge model specific config
                merged_kwargs = {**kwargs, "model": model_cfg.model, "trace_id": trace_id}
                
                result = await asyncio.wait_for(method(prompt, **merged_kwargs), timeout=model_cfg.timeout)
                
                app_logger.bind(trace_id=trace_id).success(f"✅ [SUCCESS] Request fulfilled by {model_cfg.provider}.")
                
                result.fallback_used = (i > 0)
                result.failed_providers = failed_providers
                result.trace_id = trace_id
                return result
                
            except asyncio.TimeoutError:
                err_msg = f"Request to {model_cfg.provider} timed out after {model_cfg.timeout}s"
                app_logger.bind(trace_id=trace_id).warning(f"⚠️ [TIMEOUT] {err_msg}")
                failed_providers.append({
                    "provider": model_cfg.provider, "model": model_cfg.model, 
                    "error": "TimeoutError", "message": err_msg
                })
            except Exception as e:
                err_type = type(e).__name__
                err_msg = str(e)
                app_logger.bind(trace_id=trace_id).error(f"⚠️ [FAILED] Attempt {i+1} ({model_cfg.provider}) failed: {err_type}: {err_msg}")
                failed_providers.append({
                    "provider": model_cfg.provider, "model": model_cfg.model, 
                    "error": err_type, "message": err_msg
                })
                continue
        
        error_summary = f"All providers failed for '{method_name}' route."
        app_logger.bind(trace_id=trace_id).critical(f"🚫 [CHAIN EXHAUSTED] {error_summary}")
        raise AllProvidersFailedError(error_summary, failures=failed_providers, trace_id=trace_id)

    async def generate(self, prompt: str, input_type: str = "text", output_type: str = "text", image_bytes: Optional[bytes] = None, video_bytes: Optional[bytes] = None, **kwargs) -> GenerationResult:
        trace_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Defensive Sanitization: Ensure core params aren't duplicated in kwargs
        kwargs.pop("trace_id", None)
        kwargs.pop("route", None)
        
        app_logger.bind(trace_id=trace_id).info(f"🚀 New Request: {input_type} → {output_type}")

        route = f"{input_type}→{output_type}"
        
        # Ensure trace_id and route are not in kwargs to avoid duplicate argument errors
        kwargs.pop("trace_id", None)
        kwargs.pop("route", None)
        
        try:
            if route == "text→text":
                chain = config.routing.text_generation
                result = await self._execute_with_fallback(chain, "generate_text", prompt, trace_id, **kwargs)

            elif route == "text→image":
                chain = config.routing.image_generation
                result = await self._execute_with_fallback(chain, "generate_image", prompt, trace_id, **kwargs)

            elif route == "text→audio":
                chain = config.routing.audio_generation
                result = await self._execute_with_fallback(chain, "generate_audio", prompt, trace_id, **kwargs)

            elif route == "text→video":
                chain = config.routing.video_generation
                result = await self._execute_with_fallback(chain, "generate_video", prompt, trace_id, **kwargs)

            elif route == "image→text":
                if not image_bytes:
                    raise ProviderError("No image uploaded. Please provide an image for analysis.")
                chain = config.routing.image_to_text
                
                # Force safe max_tokens for vision
                user_max_tokens = kwargs.get("max_tokens", 512)
                kwargs["max_tokens"] = min(user_max_tokens, 1024)
                
                result = await self._execute_vision_chain(chain, prompt, image_bytes, trace_id, **kwargs)

            elif route == "image→video":
                app_logger.bind(trace_id=trace_id).info("Route: image→video. Step 1: Captioning image...")
                # We use the vision chain directly for better control
                vision_chain = config.routing.image_to_text
                caption_res = await self._execute_vision_chain(vision_chain, "Describe this image in detail for a video prompt.", image_bytes, trace_id)
                
                app_logger.bind(trace_id=trace_id).info(f"Step 2: Attempting REAL video generation from caption...")
                
                # Build REAL video chain dynamically based on config
                selected_provider = config.app_settings.image_to_video_provider.lower()
                real_video_chain = []
                
                # Add only the selected provider if configured
                skipped_reason = None
                if selected_provider == "kling":
                    kling_prov = self.providers.get("kling")
                    if kling_prov and kling_prov.is_configured():
                        real_video_chain.append(ModelConfig(
                            provider="kling", 
                            model=config.app_settings.kling_image_to_video_model,
                            timeout=120
                        ))
                    else:
                        skipped_reason = "Kling skipped: KLING_API_KEY not configured or provider unavailable."
                
                elif selected_provider == "replicate":
                    repl_prov = self.providers.get("replicate")
                    if repl_prov and repl_prov.is_configured():
                        real_video_chain.append(ModelConfig(
                            provider="replicate", 
                            model=config.app_settings.replicate_image_to_video_model,
                            timeout=180
                        ))
                    else:
                        skipped_reason = "Replicate skipped: REPLICATE_API_TOKEN not configured or model invalid."
                
                real_video_result = None
                if real_video_chain:
                    try:
                        app_logger.bind(trace_id=trace_id).info(f"Chain: {[c.provider for c in real_video_chain]}")
                        real_video_result = await self._execute_with_fallback(
                            real_video_chain, "generate_video", caption_res.content, trace_id, image_bytes=image_bytes
                        )
                        result = real_video_result
                        result.metadata["is_real_video"] = True
                        result.content_type = "video"
                    except Exception as e:
                        app_logger.bind(trace_id=trace_id).warning(f"Real video generation failed, falling back to storyboard: {e}")
                
                if not real_video_result:
                    app_logger.bind(trace_id=trace_id).info("Step 3: Real video provider failed or skipped. Generating cinematic storyboard fallback...")
                    
                    final_msg = skipped_reason or "Real video generation failed. Using storyboard fallback."
                    
                    fallback_prompt = (
                        f"SYSTEM INSTRUCTION: You are a Cinematic Director. Based on this image description: '{caption_res.content}', "
                        f"create a professional cinematic storyboard and screenplay for a 10-second high-end video sequence. "
                        f"Include Camera Angles, Lighting, and Motion Description."
                    )
                    # Use storyboard chain (Groq -> Gemini)
                    text_chain = [
                        ModelConfig(provider="groq", model=config.app_settings.text_model_groq),
                        ModelConfig(provider="gemini", model=config.app_settings.gemini_vision_model)
                    ]
                    result = await self._execute_with_fallback(text_chain, "generate_text", fallback_prompt, trace_id)
                    result.content_type = "storyboard"
                    result.metadata["is_real_video"] = False
                    result.metadata["message"] = final_msg

            elif route == "video→text":
                 if not video_bytes:
                     raise ProviderError("No video uploaded. Please provide a video for analysis.")
                 app_logger.bind(trace_id=trace_id).info("Route: video→text. Extracting frames...")
                 
                 # 1. Extract frames
                 frames = extract_key_frames(video_bytes, interval_seconds=2, max_frames=8)
                 if not frames:
                     raise ProviderError("Failed to extract frames from video. The file might be corrupt or in an unsupported format.")
                 
                 app_logger.bind(trace_id=trace_id).info(f"Extracted {len(frames)} frames. Analyzing content...")
                 
                 # 2. Vision chain from config
                 chain = config.routing.video_to_text
                 
                 # Use the vision chain with frames
                 result = await self._execute_vision_chain(chain, prompt, frames, trace_id, **kwargs)
                 result.metadata.update({
                     "total_frames_extracted": len(frames),
                     "route": "Video → Text"
                 })
            else:
                raise UnsupportedRouteError(f"The route {route} is not supported.")

            # Set common metadata
            result.input_type = input_type
            result.output_type = output_type
            result.latency = time.time() - start_time

            # Cache media results
            if result.content_type in ["image", "audio", "video"]:
                ext_map = {"image": "png", "audio": "mp3", "video": "mp4"}
                extension = ext_map.get(result.content_type, "bin")
                file_path = await cache.save_media(
                    prompt, result.provider, result.content_type, 
                    result.content, extension, model=result.model, trace_id=trace_id
                )
                result.content = file_path
            
            return result

        except AllProvidersFailedError as e:
            app_logger.bind(trace_id=trace_id).error(f"All providers failed for {route}.")
            # Graceful Degradation: Text description fallback for media outputs
            if output_type != "text":
                 app_logger.bind(trace_id=trace_id).info("Attempting graceful degradation to text description...")
                 fallback_prompt = (
                    f"SYSTEM INSTRUCTION: You are a Cinematic Screenwriter. The server is busy. "
                    f"Describe the following {output_type} content vividly: {prompt}"
                )
                 try:
                     text_chain = [
                         ModelConfig(provider="groq", model=config.app_settings.text_model_groq),
                         ModelConfig(provider="gemini", model=config.app_settings.gemini_vision_model)
                     ]
                     degraded_result = await self._execute_with_fallback(text_chain, "generate_text", fallback_prompt, trace_id)
                     degraded_result.metadata["degraded"] = True
                     degraded_result.failed_providers = e.failures
                     degraded_result.input_type = input_type
                     degraded_result.output_type = output_type
                     degraded_result.latency = time.time() - start_time
                     return degraded_result
                 except Exception:
                     raise e
            raise e

    async def _execute_vision_chain(self, chain: List[ModelConfig], prompt: str, media_data: Union[bytes, List[bytes]], trace_id: str, **kwargs) -> GenerationResult:
        failures = []
        for i, model_cfg in enumerate(chain):
            provider = self.providers.get(model_cfg.provider)
            if not provider or not provider.is_configured():
                continue
            try:
                app_logger.bind(trace_id=trace_id).info(f"Vision Attempt {i+1}: {model_cfg.provider} | Model: {model_cfg.model}")
                
                # Apply provider-specific token caps
                provider_kwargs = kwargs.copy()
                if model_cfg.provider == "huggingface":
                    provider_kwargs["max_tokens"] = min(provider_kwargs.get("max_tokens", 512), 512)
                elif model_cfg.provider in ["gemini", "openrouter"]:
                    provider_kwargs["max_tokens"] = min(provider_kwargs.get("max_tokens", 1024), 1024)
                
                content = await provider.analyze_image(media_data, prompt, model=model_cfg.model, trace_id=trace_id, **provider_kwargs)
                return GenerationResult(
                    provider=model_cfg.provider,
                    model=model_cfg.model,
                    content=content,
                    content_type="text",
                    trace_id=trace_id,
                    fallback_used=(i > 0),
                    failed_providers=failures
                )
            except Exception as e:
                app_logger.bind(trace_id=trace_id).warning(f"Vision Attempt {i+1} ({model_cfg.provider}) failed: {e}")
                failures.append({
                    "provider": model_cfg.provider, 
                    "model": model_cfg.model, 
                    "error": type(e).__name__,
                    "message": str(e)
                })
        
        raise AllProvidersFailedError("All vision providers failed", failures=failures, trace_id=trace_id)

# Singleton instance
orchestrator = AsyncOrchestrator()
