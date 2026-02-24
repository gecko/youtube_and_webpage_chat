"""Core application controller that holds conversation state and business logic.

This module does not perform direct I/O (no print/input) and depends on injected
service objects for LLM client and transcript fetching.
"""

import os
from typing import List, Dict, Optional

from dotenv import load_dotenv


def _parse_youtube_video_id(url: str) -> Optional[str]:
    try:
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        if "youtu.be" in url:
            return url.rstrip("/").split("/")[-1]
        # fallback: last path segment
        return url.rstrip("/").split("/")[-1]
    except Exception:
        return None


class ContentController:
    def __init__(self, llm_client, fetcher, default_model: Optional[str] = None, context_size: int = 32000):
        load_dotenv()
        self.llm_client = llm_client
        self.fetcher = fetcher
        self.context_size = context_size
        self.available_models: List[str] = []

        # Load or set current model
        if default_model:
            self.current_model = default_model
        else:
            self.current_model = os.getenv("SELECTED_MODEL", "")

        self.transcript: str = ""
        self.messages: List[Dict[str, str]] = []
        self.source_type: Optional[str] = None
        self.loaded_url: Optional[str] = None

    def ensure_models(self) -> None:
        if not self.available_models:
            self.available_models = self.llm_client.list_models()
            if not self.current_model and self.available_models:
                self.current_model = self.available_models[0]

    def list_models(self) -> List[str]:
        self.ensure_models()
        return self.available_models[:]

    def set_model(self, model: str) -> None:
        self.ensure_models()
        if model not in self.available_models:
            raise ValueError("Model not available")
        self.current_model = model
        # Persist to .env
        os.makedirs(os.path.dirname(os.path.abspath(".env")) or ".", exist_ok=True)
        self._save_env_var("SELECTED_MODEL", model)

    def load(self, url: str) -> str:
        self.loaded_url = url
        if any(x in url for x in ("youtube.com", "youtu.be", "watch?v=")):
            video_id = _parse_youtube_video_id(url)
            if not video_id:
                raise ValueError("Could not parse YouTube video ID")
            self.transcript = self.fetcher.fetch_youtube(video_id)
            self.source_type = "youtube"
        else:
            self.transcript = self.fetcher.fetch_webpage(url)
            self.source_type = "webpage"

        self._initialize_chat_messages()
        return self.transcript

    def _initialize_chat_messages(self) -> None:
        dont_consider_advertisements_prompt = (
            "Also, when analyzing the content, ignore any advertisements, "
            "promotional material, or unrelated links that may be present. "
            "Focus solely on the main content relevant to the topic at hand. "
        )
        if self.source_type == "webpage":
            system_msg = (
                "You are an intelligent assistant analyzing the contents of a webpage. "
                + "Use only the provided webpage text as your context. "
                + "Provide clear, concise, and accurate answers focused on the content. "
                + "When appropriate, organize information into bullet lists for clarity. "
                + "Avoid speculation beyond the text and maintain a helpful tone. "
                + dont_consider_advertisements_prompt
            )
            user_msg = f"Here is the webpage content (from {self.loaded_url}):\n{self.transcript}"
            assistant_msg = "I have received the webpage content. You can now ask me questions about the page."
        elif self.source_type == "youtube":
            system_msg = (
                "You are an assistant discussing a YouTube video using only the provided subtitles as your context. "
                "Focus your responses on the video's content based on these subtitles. Keep your answers clear, concise, and informative. "
                "Use bullet lists when it helps to organize key points or steps. Avoid making assumptions beyond the subtitles."
                + dont_consider_advertisements_prompt
            )
            user_msg = f"Here are the subtitles:\n{self.transcript}"
            assistant_msg = "I have received the subtitles. You can now ask me questions about the video."
        else:
            system_msg = (
                "You are an assistant. If given, use the provided content as context and keep your answers clear, concise, and informative. "
                + "Use bullet lists when it helps to organize key points or steps."
            )
            user_msg = f"Here is the content:\n{self.transcript}"
            assistant_msg = "I have received the content. You can now ask me questions."

        self.messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]

    def summarize(self) -> str:
        if not self.transcript:
            raise RuntimeError("No content loaded to summarize")

        # Ensure a model is selected before making API calls
        self.ensure_models()

        summary_prompt = "Please provide a brief summary of the following content:\n"
        summary_prompt += "<CONTENT>\n"
        summary_prompt += f"{self.transcript}\n"
        summary_prompt += "</CONTENT>\n"
        summary_prompt += "Please keep the summary concise and to the point."
        self.messages.append({"role": "user", "content": summary_prompt})
        response = self.llm_client.chat(
            model=self.current_model,
            messages=self.messages,
            options={"num_ctx": self.context_size},
        )
        return response["message"]["content"]

    def ask(self, user_input: str) -> str:
        if not user_input.strip():
            raise ValueError("Empty user input")

        # Ensure a model is selected before making API calls
        self.ensure_models()

        self.messages.append({"role": "user", "content": user_input})
        response = self.llm_client.chat(
            model=self.current_model, messages=self.messages, options={"num_ctx": self.context_size}
        )
        assistant_message = response["message"]
        self.messages.append(assistant_message)
        return assistant_message["content"]

    def clear_history(self) -> None:
        if self.transcript:
            self._initialize_chat_messages()
        else:
            self.messages = []

    def reset(self) -> None:
        self.__init__(self.llm_client, self.fetcher)

    def swap_llm_client(self, new_client) -> None:
        """Swap the LLM client while preserving conversation history.

        This allows switching between providers (e.g., Ollama to OpenRouter)
        without losing the conversation context. Automatically selects the first
        available model from the new provider and saves it to .env.

        Args:
            new_client: The new LLM client instance
        """
        self.llm_client = new_client
        self.available_models = []  # Reset cached models
        
        # Automatically fetch models from new provider and select the first one
        try:
            self.available_models = self.llm_client.list_models()
            if self.available_models:
                self.current_model = self.available_models[0]
                # Persist the selected model to .env
                self._save_env_var("SELECTED_MODEL", self.current_model)
        except Exception:
            # If unable to fetch models, reset current_model
            self.current_model = ""

    @staticmethod
    def _save_env_var(key: str, value: str) -> None:
        """Save an environment variable to .env file."""
        env_file = ".env"

        # Read existing content
        existing_content = ""
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
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
        with open(env_file, "w") as f:
            f.write("\n".join(lines) + "\n")
