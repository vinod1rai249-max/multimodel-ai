import socket
from core.logger import app_logger

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
        results[name] = is_up
        if not is_up:
            app_logger.error(f"DNS lookup failed for {name} ({host}).")
        else:
            app_logger.info(f"DNS lookup successful for {name}.")
    
    return results
