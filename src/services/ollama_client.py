"""Lightweight wrapper around the `ollama` module to enable DI and easier testing.

This module intentionally avoids any network or side-effect in constructors.
Implements the LLMClient protocol for compatibility with other LLM backends.
"""

from typing import Any, Dict, List

import ollama

from . import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, client_module: Any = ollama):
        self._client = client_module

    def list_models(self) -> List[str]:
        try:
            return [m["model"] for m in self._client.list()["models"]]
        except Exception as exc:  # Keep narrow in higher-level code if needed
            raise RuntimeError(f"Error listing Ollama models: {exc}") from exc

    def chat(self, model: str, messages: list, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        try:
            return self._client.chat(model=model, messages=messages, options=options or {})
        except Exception as exc:
            raise RuntimeError(f"Error calling Ollama.chat: {exc}") from exc
