"""
Centralized Gemini API client manager for performance optimization.
Provides singleton clients with connection pooling and caching.
"""

import json
from pathlib import Path
from google import genai
from typing import Optional

_client_cache = {}
_api_key_cache = None


def get_api_key() -> str:
    """Get API key with caching to avoid repeated file reads."""
    global _api_key_cache
    if _api_key_cache is None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
        with open(config_path, "r", encoding="utf-8") as f:
            _api_key_cache = json.load(f)["gemini_api_key"]
    return _api_key_cache


def get_client(model_name: str = "gemini-2.5-flash") -> genai.Client:
    """
    Get a cached Gemini client instance.
    Reuses clients to avoid repeated initialization overhead.
    
    Args:
        model_name: The model to use (default: gemini-2.5-flash)
    
    Returns:
        Configured Gemini client
    """
    cache_key = f"client_{model_name}"
    
    if cache_key not in _client_cache:
        _client_cache[cache_key] = genai.Client(
            api_key=get_api_key(),
            http_options={"api_version": "v1alpha"}
        )
    
    return _client_cache[cache_key]


def get_model(model_name: str = "gemini-2.5-flash", **config):
    """
    Get a Gemini model wrapper for generate_content calls.
    
    Args:
        model_name: Model name (e.g., 'gemini-2.5-flash', 'gemini-2.0-flash-lite')
        **config: Additional configuration (e.g., system_instruction, temperature, etc.)
    
    Returns:
        Model wrapper with generate_content method
    """
    client = get_client(model_name)
    
    class ModelWrapper:
        def __init__(self, client, model_name, **config):
            self._client = client
            self._model_name = model_name
            self._config = config
        
        def generate_content(self, prompt, **kwargs):
            """Generate content using the new API."""
            # Merge config and kwargs
            merged_config = {**self._config, **kwargs}
            
            # Handle system_instruction specially
            system_instruction = merged_config.pop('system_instruction', None)
            
            # Build contents with system instruction if provided
            if system_instruction:
                contents = [
                    {"role": "user", "parts": [{"text": system_instruction}]},
                    {"role": "model", "parts": [{"text": "Understood."}]},
                    {"role": "user", "parts": [{"text": str(prompt)}]}
                ]
            else:
                contents = prompt
            
            return self._client.models.generate_content(
                model=self._model_name,
                contents=contents,
                **merged_config
            )
    
    return ModelWrapper(client, model_name, **config)


def clear_cache():
    """Clear all cached clients (useful for testing or key rotation)."""
    global _client_cache, _api_key_cache
    _client_cache.clear()
    _api_key_cache = None
