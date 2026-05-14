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


def get_model(model_name: str = "gemini-2.5-flash"):
    """
    Get a Gemini model instance using the new google.genai API.
    
    Args:
        model_name: Model name (e.g., 'gemini-2.5-flash', 'gemini-2.0-flash-lite')
    
    Returns:
        Model instance for generate_content calls
    """
    client = get_client(model_name)
    return client.models.generate_content


def clear_cache():
    """Clear all cached clients (useful for testing or key rotation)."""
    global _client_cache, _api_key_cache
    _client_cache.clear()
    _api_key_cache = None
