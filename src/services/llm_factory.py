"""Factory for creating LLM client instances based on user selection."""

import os
from typing import Union

from dotenv import load_dotenv

from .ollama_client import OllamaClient
from .openrouter_client import OpenRouterClient
from . import LLMClient


def create_llm_client(
    renderer: "RichRenderer | None" = None, force_interactive: bool = False
) -> Union[OllamaClient, OpenRouterClient]:
    """Create and return an LLM client based on user selection or .env configuration.

    This function:
    1. Checks .env for SELECTED_LLM_PROVIDER (unless force_interactive=True)
    2. If not set or force_interactive, prompts user interactively
    3. Validates provider-specific requirements (e.g., API key for OpenRouter)
    4. Saves selection to .env for persistence

    Args:
        renderer: Optional RichRenderer for user output. If None, uses print statements.
        force_interactive: If True, always prompt for provider selection regardless of .env setting.

    Returns:
        Instantiated LLM client (OllamaClient or OpenRouterClient)

    Raises:
        RuntimeError: If provider validation fails
    """
    load_dotenv()

    selected_provider = "" if force_interactive else os.getenv("SELECTED_LLM_PROVIDER", "").strip()

    if not selected_provider:
        # Interactive provider selection
        selected_provider = _prompt_provider_selection(renderer)
        _save_env_var("SELECTED_LLM_PROVIDER", selected_provider)

    if selected_provider.lower() == "ollama":
        return OllamaClient()
    elif selected_provider.lower() == "openrouter":
        return _create_openrouter_client(renderer)
    else:
        raise RuntimeError(f"Unknown LLM provider: {selected_provider}")


def _prompt_provider_selection(renderer: "RichRenderer | None" = None) -> str:
    """Prompt user to select an LLM provider.

    Args:
        renderer: Optional RichRenderer for styled output

    Returns:
        Selected provider name ('ollama' or 'openrouter')
    """
    if renderer:
        renderer.render_plain("\n[bold cyan]Select LLM Provider[/bold cyan]")
        renderer.render_plain("  (1) Ollama (local, requires Ollama running)")
        renderer.render_plain("  (2) OpenRouter (free tier models, requires API key)")
    else:
        print("\nSelect LLM Provider:")
        print("  (1) Ollama (local, requires Ollama running)")
        print("  (2) OpenRouter (free tier models, requires API key)")

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            return "ollama"
        elif choice == "2":
            return "openrouter"
        else:
            print("Invalid choice. Please enter 1 or 2.")


def _create_openrouter_client(renderer: "RichRenderer | None" = None) -> OpenRouterClient:
    """Create OpenRouter client, validating API key.

    Args:
        renderer: Optional RichRenderer for styled output

    Returns:
        Instantiated OpenRouterClient

    Raises:
        RuntimeError: If API key is not configured
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        msg = (
            "\n[bold red]OpenRouter API key not found![/bold red]\n"
            "Please add your API key to the .env file:\n"
            "  OPENROUTER_API_KEY=your_api_key_here\n"
            "\nYou can get a free API key at: https://openrouter.ai/keys"
        )
        if renderer:
            renderer.render_error(msg)
        else:
            print(msg)
        raise RuntimeError("OpenRouter API key not configured in .env file")

    return OpenRouterClient(api_key=api_key)


def _save_env_var(key: str, value: str) -> None:
    """Save an environment variable to .env file, creating it if necessary.

    Args:
        key: Environment variable name
        value: Environment variable value
    """
    env_file = ".env"
    env_path = os.path.expanduser(f"~/.youtube_subs_{env_file}") if not os.path.exists(env_file) else env_file

    # Read existing content
    existing_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            existing_content = f.read()

    # Update or append the key
    lines = existing_content.strip().split("\n") if existing_content.strip() else []
    updated = False

    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}")

    # Write back to file
    with open(env_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Also update the current process environment
    os.environ[key] = value
