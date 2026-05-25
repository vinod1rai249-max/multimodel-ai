import socket
from core.logger import app_logger
from core.config_loader import config as app_config

def check_dns(host: str) -> bool:
    try:
        socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False

def run_diagnostics():
    endpoints = {
        "Gemini": "generativelanguage.googleapis.com",
        "Groq": "api.groq.com",
        "HuggingFace": "api-inference.huggingface.co",
        "OpenRouter": "openrouter.ai"
    }
    
    results = {}
    for name, host in endpoints.items():
        is_up = check_dns(host)
        
        # Also check API key configuration
        key_map = {
            "Gemini": "GEMINI_API_KEY",
            "Groq": "GROQ_API_KEY",
            "HuggingFace": "HF_TOKEN",
            "OpenRouter": "OPENROUTER_API_KEY"
        }
        key_name = key_map.get(name)
        has_key = app_config.api_keys.get(key_name) is not None
        
        results[name] = {
            "dns": is_up,
            "configured": has_key,
            "host": host
        }
        
        if not is_up:
            app_logger.error(f"DNS lookup failed for {name} ({host}).")
        if not has_key:
            app_logger.warning(f"API Key {key_name} is NOT configured.")
            
    return results
