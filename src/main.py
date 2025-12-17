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

# make the `src` directory importable so `services` and `app` modules resolve
sys.path.insert(0, os.path.dirname(__file__))

from services.ollama_client import OllamaClient
from services.content_fetcher import ContentFetcher
from app.controller import ContentController


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
    intro = "Welcome. Type /help for commands, or just chat."
    prompt = "> "

    def __init__(self, controller: ContentController):
        super().__init__()
        self.controller = controller
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
        print("Commands: /load <url>, /model, /summary, /subs, /hist, /clear, /reset, /exit")

    def do_load(self, arg):
        url = arg or input("Enter URL: ")
        try:
            self.controller.load(url)
            print("Loaded content.")
        except Exception as exc:
            print(f"Error loading URL: {exc}")

    def do_model(self, arg):
        try:
            models = self.controller.list_models()
            for i, m in enumerate(models):
                prefix = "*" if m == self.controller.current_model else " "
                print(f"{i}: {prefix} {m}")
            sel = input("Select model index or name: ")
            try:
                idx = int(sel)
                self.controller.set_model(models[idx])
            except Exception:
                self.controller.set_model(sel)
            print(f"Using model: {self.controller.current_model}")
        except Exception as exc:
            print(f"Error selecting model: {exc}")

    def do_summary(self, arg):
        try:
            summary = self.controller.summarize()
            print("--- SUMMARY ---")
            print(summary)
        except Exception as exc:
            print(f"Error generating summary: {exc}")

    def do_subs(self, arg):
        print(self.controller.transcript or "(no content)")

    def do_hist(self, arg):
        for i, m in enumerate(self.controller.messages):
            content_preview = m.get("content", "")[:100].replace("\n", " ")
            print(f"[{i}] {m.get('role','?')}: {content_preview}")

    def do_clear(self, arg):
        self.controller.clear_history()
        print("Cleared history")

    def do_reset(self, arg):
        self.controller.reset()
        print("Reset controller")

    def do_cls(self, arg):
        os.system("cls" if os.name == "nt" else "clear")

    def do_exit(self, arg):
        print("Goodbye!")
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

            if not self.controller.transcript:
                print("⚠️ Note that there is no content loaded. Use /load <url> to load a resource.")

            print("Assistant: Thinking...")
            reply = self.controller.ask(line)
            print(f"Assistant: {reply}")
        except Exception as exc:
            print(f"Error while asking model: {exc}")


def main():
    _setup_history()

    ollama_client = OllamaClient()
    fetcher = ContentFetcher()
    controller = ContentController(ollama_client, fetcher)

    try:
        models = controller.list_models()
        print(f"Available models: {len(models)}. Default: {controller.current_model}")
    except Exception as exc:
        print(f"Warning: could not list Ollama models: {exc}")

    print("Type /help for available commands.")
    cli = ChatCLI(controller)
    cli.cmdloop()


if __name__ == "__main__":
    main()
