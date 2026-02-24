"""OpenRouter LLM client for accessing free tier models via OpenRouter API."""

import os
import requests
from typing import Any, Dict, List

# OpenRouter API constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


class OpenRouterClient:
    """Client for interacting with free tier models via OpenRouter API."""

    def __init__(self, api_key: str | None = None):
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key. If None, attempts to load from OPENROUTER_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided and OPENROUTER_API_KEY env var is not set.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )
        self._free_models_cache: List[str] | None = None

    def list_models(self) -> List[str]:
        """Return the OpenRouter free tier routing model.

        OpenRouter's '/free' model intelligently routes requests to available
        free tier models, so we don't need to fetch or list individual models.

        Returns:
            List containing just the openrouter/free routing model

        Raises:
            RuntimeError: If unable to validate the API key
        """
        try:
            # Validate API key by making a lightweight request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/danie1fs/youtube_and_webpage_chat",
            }
            # Just do a HEAD request to validate the key works
            response = requests.head("https://openrouter.ai/api/v1/models", headers=headers, timeout=5)
            if response.status_code >= 400:
                raise RuntimeError(f"OpenRouter API validation failed: {response.status_code}")
            return ["openrouter/free"]
        except Exception as exc:
            raise RuntimeError(f"Error validating OpenRouter API: {exc}") from exc

    def chat(self, model: str, messages: list, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Send a chat request to OpenRouter using the free routing model.

        Args:
            model: The OpenRouter model identifier (should be 'openrouter/free')
            messages: List of message dicts with 'role' and 'content' keys
            options: Optional dict with parameters (ignored for OpenRouter)

        Returns:
            Response dict with 'message' key containing assistant response

        Raises:
            RuntimeError: If the chat request fails
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/danie1fs/youtube_and_webpage_chat",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model,
                "messages": messages,
            }

            response = requests.post(
                f"{OPENROUTER_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            data = response.json()
            # Convert OpenRouter response format to match Ollama format
            assistant_message = data["choices"][0]["message"]["content"]
            return {
                "message": {
                    "role": "assistant",
                    "content": assistant_message,
                }
            }
        except Exception as exc:
            raise RuntimeError(f"Error calling OpenRouter.chat: {exc}") from exc
