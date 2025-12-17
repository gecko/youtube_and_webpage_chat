"""Encapsulates fetching content from YouTube and extracting text from webpages.

Provides a unified interface for fetching textual content (YouTube transcripts
or webpage text). This replaces the older `TranscriptFetcher` name to better
reflect support for multiple content sources.
"""

from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import requests
from bs4 import BeautifulSoup


class ContentFetcher:
    def fetch_youtube(self, video_id: str) -> str:
        try:
            ytt_api = YouTubeTranscriptApi()
            fetched = ytt_api.fetch(video_id, languages=["de", "en"])
            texts = []
            for snippet in fetched:
                if isinstance(snippet, dict):
                    texts.append(snippet.get("text", ""))
                else:
                    texts.append(getattr(snippet, "text", ""))
            return " ".join(t for t in texts if t)
        except TranscriptsDisabled as exc:
            raise RuntimeError("Transcripts are disabled for this video") from exc
        except Exception as exc:
            raise RuntimeError(f"Error fetching YouTube transcript: {exc}") from exc

    def fetch_webpage(self, url: str, timeout: int = 10) -> str:
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for s in soup(["script", "style"]):
                s.extract()
            chunks = list(soup.stripped_strings)
            if not chunks:
                raise RuntimeError("No textual content extracted from webpage")
            return " ".join(chunks)
        except Exception as exc:
            raise RuntimeError(f"Error fetching webpage content: {exc}") from exc
