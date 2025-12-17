import pytest
from unittest.mock import Mock

from app.controller import ContentController


def make_controller(mock_ollama=None, mock_fetcher=None):
    # Only set defaults when a mock isn't provided by the caller
    if mock_ollama is None:
        mock_ollama = Mock()
        mock_ollama.list_models.return_value = ["model-a", "model-b"]
        mock_ollama.chat.return_value = {"message": {"content": "ok", "role": "assistant"}}

    if mock_fetcher is None:
        mock_fetcher = Mock()

    return ContentController(mock_ollama, mock_fetcher)


def test_list_models_lazy_fetch():
    mock_ollama = Mock()
    mock_ollama.list_models.return_value = ["m1"]
    ctrl = make_controller(mock_ollama=mock_ollama)
    models = ctrl.list_models()
    assert models == ["m1"]
    assert ctrl.current_model == "m1"


def test_load_webpage_initializes_messages():
    mock_fetcher = Mock()
    mock_fetcher.fetch_webpage.return_value = "This is page text"
    ctrl = make_controller(mock_fetcher=mock_fetcher)
    content = ctrl.load("https://example.com/page")
    assert "page text" in content
    assert ctrl.source_type == "webpage"
    assert any(m["role"] == "system" for m in ctrl.messages)


def test_summarize_calls_ollama():
    mock_ollama = Mock()
    mock_ollama.list_models.return_value = ["m1"]
    mock_ollama.chat.return_value = {"message": {"content": "SUMMARY"}}
    mock_fetcher = Mock()
    mock_fetcher.fetch_webpage.return_value = "a b c"
    ctrl = ContentController(mock_ollama, mock_fetcher)
    ctrl.load("https://example.com")
    res = ctrl.summarize()
    assert res == "SUMMARY"


def test_ask_appends_messages_and_returns_text():
    mock_ollama = Mock()
    mock_ollama.list_models.return_value = ["m1"]
    mock_ollama.chat.return_value = {"message": {"content": "reply", "role": "assistant"}}
    ctrl = ContentController(mock_ollama, Mock())
    ctrl.messages = [{"role": "system", "content": "ctx"}]
    reply = ctrl.ask("Hello")
    assert reply == "reply"
    assert any(m["role"] == "assistant" for m in ctrl.messages)
