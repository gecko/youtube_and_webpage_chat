"""Services module: LLM clients and content fetchers."""

from typing import Protocol, Any, Dict, List


class LLMClient(Protocol):
    """Protocol for LLM client implementations (Ollama, OpenRouter, etc.)."""

    def list_models(self) -> List[str]:
        """Return a list of available model names.

        Returns:
            List of model identifiers

        Raises:
            RuntimeError: If unable to fetch models
        """
        ...

    def chat(self, model: str, messages: list, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Send a chat request to the LLM.

        Args:
            model: The model identifier to use
            messages: List of message dicts with 'role' and 'content' keys
            options: Optional dict with model-specific parameters

        Returns:
            Response dict with 'message' key containing the assistant's response

        Raises:
            RuntimeError: If the chat request fails
        """
        ...
