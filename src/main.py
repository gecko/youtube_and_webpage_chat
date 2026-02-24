"""Command-line interface entrypoint using a cmd-based shell with tab completion.

This file wires the `ContentController` to a `cmd.Cmd` interactive shell so that
tab-completion, history, and readline features work on Windows via the installed
readline implementation.
"""

import sys
import os
import readline
import atexit
import cmd
from time import time

from dotenv import load_dotenv

# make the `src` directory importable so `services` and `app` modules resolve
sys.path.insert(0, os.path.dirname(__file__))

from services.llm_factory import create_llm_client
from services.content_fetcher import ContentFetcher
from app.controller import ContentController
from renderers.rich_renderer import RichRenderer


HISTORY_FILE = os.path.expanduser("~/.youtube_subs_history")
EXIT_COMMANDS = {"/exit", "/quit", "/bye"}


def _setup_history():
    try:
        readline.read_history_file(HISTORY_FILE)
    except Exception:
        pass

    def _save():
        try:
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass

    atexit.register(_save)


class ChatCLI(cmd.Cmd):
    intro = ""
    prompt = "\n> "

    def __init__(self, controller: ContentController, renderer: RichRenderer):
        super().__init__()
        self.controller = controller
        self.renderer = renderer
        # load history if available
        try:
            if os.path.exists(HISTORY_FILE):
                readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass
        readline.set_history_length(1000)

    # Provide slash-based completion for command names
    def completenames(self, text, *ignored):
        if text.startswith("/"):
            text = text[1:]
            return ["/" + name[3:] for name in self.get_names() if name.startswith("do_" + text)]
        return super().completenames(text, *ignored)

    def precmd(self, line):
        # allow users to type commands with a leading slash
        if line.startswith("/"):
            return line[1:]
        return line

    def do_help(self, arg):
        self.renderer.render_help()

    def do_load(self, arg):
        url = arg or input("Enter URL: ")
        try:
            self.controller.load(url)
            self.renderer.render_success("Loaded content.")
        except Exception as exc:
            self.renderer.render_error(f"Error loading URL: {exc}")

    def do_provider(self, arg):
        """Switch between LLM providers (Ollama or OpenRouter)."""
        try:
            from services.llm_factory import create_llm_client
            import os

            new_client = create_llm_client(self.renderer, force_interactive=True)
            self.controller.swap_llm_client(new_client)

            # Get provider name for feedback
            provider_name = os.getenv("SELECTED_LLM_PROVIDER", "unknown").lower()
            if provider_name == "ollama":
                provider_display = "Ollama"
            elif provider_name == "openrouter":
                provider_display = "OpenRouter"
            else:
                provider_display = provider_name

            self.renderer.render_success(f"Switched to {provider_display}. Conversation history preserved.")
        except Exception as exc:
            self.renderer.render_error(f"Error switching provider: {exc}")

    def do_model(self, arg):
        try:
            models = self.controller.list_models()
            if arg:
                sel = arg
            else:
                self.renderer.render_models_table(models, self.controller.current_model)
                sel = input("Select model index or name: ")
            try:
                idx = int(sel)
                self.controller.set_model(models[idx])
            except Exception:
                self.controller.set_model(sel)
            self.renderer.render_success(f"Using model: {self.controller.current_model}")
        except Exception as exc:
            self.renderer.render_error(f"Error selecting model: {exc}")

    def do_summary(self, arg):
        try:
            t_start = time()
            summary = self.controller.summarize()
            t_end = time()
            self.renderer.render_summary(summary)
            self.renderer.render_caption(f"{t_end - t_start:.2f} seconds")
        except Exception as exc:
            self.renderer.render_error(f"Error generating summary: {exc}")

    def do_subs(self, arg):
        if self.controller.transcript:
            self.renderer.render_plain(self.controller.transcript)
            self.renderer.render_caption(f"Length: {len(self.controller.transcript.split())} words")
        else:
            self.renderer.render_warning("No content loaded")

    def do_ctx(self, arg):
        try:
            size = int(arg) if arg else None
            if size:
                self.controller.context_size = size
                self.renderer.render_success(f"Set context size to {self.controller.context_size} characters")
            else:
                self.renderer.render_plain(f"Current context size: {self.controller.context_size} characters")
        except Exception as exc:
            self.renderer.render_error(f"Error setting context size: {exc}")

    def do_timing(self, arg):
        pass  # Timing command implementation can be added here

    def do_hist(self, arg):
        self.renderer.render_history(self.controller.messages)

    def do_clear(self, arg):
        self.controller.clear_history()
        self.renderer.render_success("Cleared history")

    def do_reset(self, arg):
        self.controller.reset()
        self.renderer.render_success("Reset controller")

    def do_cls(self, arg):
        os.system("cls" if os.name == "nt" else "clear")

    def do_exit(self, arg):
        self.renderer.render_success("Goodbye!")
        return True

    def do_bye(self, arg):
        return self.do_exit(arg)

    def default(self, line):
        # if the controller can handle slash commands, let it (but we already strip / in precmd)
        if not line.strip():
            return
        try:
            if line.startswith("/"):
                # handled by precmd/onecmd
                return
            self.renderer.render_loading_message()
            t_start = time()
            reply = self.controller.ask(line)
            t_end = time()
            self.renderer.render_response("assistant", reply)
            self.renderer.render_caption(f"{t_end - t_start:.2f} seconds")
        except Exception as exc:
            self.renderer.render_error(f"Error while asking model: {exc}")


def main():
    _setup_history()
    load_dotenv()

    llm_client = create_llm_client(renderer=None)
    fetcher = ContentFetcher()
    controller = ContentController(llm_client, fetcher)
    renderer = RichRenderer()

    renderer.render_help()
    
    # Display selected provider and model at startup
    provider_name = os.getenv("SELECTED_LLM_PROVIDER", "ollama").lower()
    if provider_name == "ollama":
        provider_display = "Ollama"
    elif provider_name == "openrouter":
        provider_display = "OpenRouter"
    else:
        provider_display = provider_name
    
    model_display = controller.current_model or "Not selected"
    renderer.render_plain(f"\n[bold green]→ Provider:[/bold green] {provider_display}  |  [bold green]Model:[/bold green] {model_display}\n")
    
    cli = ChatCLI(controller, renderer)
    cli.cmdloop()


if __name__ == "__main__":
    main()
