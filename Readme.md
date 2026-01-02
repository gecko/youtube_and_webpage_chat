# Youtube & Webpage Chat

A small CLI tool to load YouTube subtitles or webpage text and chat about the content using a local Ollama model.

**Features**
- Load YouTube transcripts (when available) or scrape webpage text
- Ask questions, get summaries, and interact with the loaded content via a local Ollama model
- Select from available Ollama models and adjust context size
- Nice CLI: tab-completion for commands and persistent command/history accessible with the arrow keys

**Requirements**
- Python 3.11 – 3.14
- Ollama running locally and reachable from this machine
- Network access for fetching YouTube transcripts and webpages

**Install**
1. Install Poetry (optional but recommended):

```bash
pip install poetry
```

2. Install dependencies:

```bash
poetry install
```

You can run the test-suite with Poetry:

```bash
poetry run pytest -q
```

**Run**

```bash
poetry run python src/main.py
```

The app starts a small REPL. Type `/help` to see available commands.

CLI tips:
- Use Tab to complete commands (e.g. type `/lo` then press Tab for `/load`).
- Use Up/Down arrow keys to traverse previous commands and messages.

**Common Commands**
- `/load <url>` — Load a YouTube video or webpage URL
- `/model` — List and choose an Ollama model
- `/subs` — Print the full loaded content (subtitles or webpage text)
- `/summary` — Ask the model for a concise summary of the loaded content
- `/hist` — Show the chat history used as context for the model
- `/csize` — Show current word count in context
- `/setcwindow <token>` — Set model context window size
- `/clear` — Clear the chat history (keeps loaded content)
- `/reset` — Reset the whole application state
- `/cls` — Clear the terminal screen
- `/help` — Show help
- `/exit` — Quit the app

**Notes & Troubleshooting**
- Ollama must be running locally. If `src/main.py` cannot list models, ensure Ollama is started and reachable.
- Some YouTube videos have transcripts disabled; the tool will report this.
- To change the default Ollama model, edit the `DEFAULT_MODEL` constant in [src/main.py](src/main.py).

**Architecture (high level)**
- `src/services/ollama_client.py` — small wrapper around the `ollama` module (list models, chat). This enables dependency injection and easier testing.
- `src/services/content_fetcher.py` — encapsulates YouTube transcript fetching and webpage text extraction (BeautifulSoup) and provides a single `ContentFetcher` interface for different sources.
- `src/app/controller.py` — core business logic, maintains conversation state and provides pure methods: `load()`, `summarize()`, `ask()`, `clear_history()`, `reset()`.
- `src/main.py` — thin CLI adapter built on `cmd.Cmd`, responsible only for user I/O, history, and tab completion; it delegates work to the controller.

This separation keeps I/O and third-party integrations separate from the pure application logic, improving testability and maintainability.

**Directory structure**
```
youtube_subs/
├── src/
│   ├── main.py                # CLI entrypoint
│   ├── app/
│   │   └── controller.py      # core business logic
│   └── renderers/
│       └── rich_renderer.py   # print text in CLI nicer
│   └── services/
│       ├── ollama_client.py   # small wrapper around Ollama
│       └── content_fetcher.py # fetch YouTube transcripts & webpage text
├── tests/                     # unit tests
│   ├── conftest.py
│   └── test_controller.py
├── Readme.md
└── pyproject.toml
```

**Architecture diagram (boxed)**
```
┌─────────────────┐     ┌─────────────────────────────────────┐
│      User       │ <-> │ CLI: tab-shell (uses Rich-renderer) │
└─────────────────┘     └─────────────────────────────────────┘
		    					    		│
		    	    						▼
		    				 ┌────────────────────────────┐
		    				 │  ContentController (core)  │
		    				 │  (business logic / state)  │
		    				 └────────────────────────────┘
		    		        	 ↙                    ↘
	        	┌─────────────────────┐         ┌──────────────────────┐
	        	│   ContentFetcher    │         │     OllamaClient     │
	        	│   (YouTube / Web)   │         │   (list/chat API)    │
	        	└─────────────────────┘         └──────────────────────┘
```

**Development**
- The project metadata and dependencies are defined in [pyproject.toml](pyproject.toml).
- To run the script directly without Poetry (assuming your environment has dependencies installed):

```bash
python src/main.py
```
