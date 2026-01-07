"""Core application controller that holds conversation state and business logic.

This module does not perform direct I/O (no print/input) and depends on injected
service objects for Ollama and transcript fetching.
"""

from typing import List, Dict, Optional


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
    def __init__(self, ollama_client, fetcher, default_model: Optional[str] = None, context_size: int = 32000):
        self.ollama = ollama_client
        self.fetcher = fetcher
        self.context_size = context_size
        self.available_models: List[str] = []
        self.current_model: Optional[str] = default_model
        self.transcript: str = ""
        self.messages: List[Dict[str, str]] = []
        self.source_type: Optional[str] = None
        self.loaded_url: Optional[str] = None

    def ensure_models(self) -> None:
        if not self.available_models:
            self.available_models = self.ollama.list_models()
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
        if self.source_type == "webpage":
            system_msg = "You are a helpful assistant that summarizes webpage content."
            body_label_start = "<WEBPAGE_START>\n"
            body_label_end = "<WEBPAGE_END>\n"
        else:
            system_msg = "You are a helpful assistant that summarizes YouTube video subtitles."
            body_label_start = "<SUBTITLES_START>\n"
            body_label_end = "<SUBTITLES_END>\n"

        summary_prompt = "Please provide a brief summary of the following content:\n"
        summary_prompt += body_label_start
        summary_prompt += f"{self.transcript}\n"
        summary_prompt += body_label_end
        summary_prompt += "Please keep the summary concise and to the point."

        response = self.ollama.chat(
            model=self.current_model,
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": summary_prompt}],
            options={"num_ctx": self.context_size},
        )
        return response["message"]["content"]

    def ask(self, user_input: str) -> str:
        if not user_input.strip():
            raise ValueError("Empty user input")
        self.messages.append({"role": "user", "content": user_input})
        response = self.ollama.chat(
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
        self.__init__(self.ollama, self.fetcher)
