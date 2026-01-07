"""Rich terminal renderer for formatted console output.

Encapsulates all Rich formatting logic and provides a clean interface
for the CLI to render responses, errors, and other UI elements.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class RichRenderer:
    """Handles all terminal rendering using Rich library."""

    def __init__(self):
        self.console = Console()

    def render_response(self, role: str, content: str) -> None:
        """Render a chat message with role-based styling.

        Args:
            role: The role of the message sender (e.g., 'assistant', 'user')
            content: The message content, may contain markdown
        """
        if role == "assistant":
            # Render assistant responses as markdown with cyan styling
            self.console.print(Markdown(content), style="cyan")
        elif role == "user":
            self.console.print(f"[bold blue]You:[/bold blue] {content}", highlight=False)
        else:
            self.console.print(f"[bold]{role}:[/bold] {content}", highlight=False)

    def render_summary(self, summary: str) -> None:
        """Render a summary in a highlighted panel.

        Args:
            summary: The summary text, may contain markdown
        """
        self.console.print(
            Panel(
                Markdown(summary),
                title="[bold green]Summary[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    def render_error(self, message: str) -> None:
        """Render an error message with red styling.

        Args:
            message: The error message text
        """
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def render_success(self, message: str) -> None:
        """Render a success message with green styling.

        Args:
            message: The success message text
        """
        self.console.print(f"[bold green]✓[/bold green] {message}", highlight=False)

    def render_warning(self, message: str) -> None:
        """Render a warning message with yellow styling.

        Args:
            message: The warning message text
        """
        self.console.print(f"[bold yellow]⚠️[/bold yellow] {message}")

    def render_models_table(self, models: list, current_model: str) -> None:
        """Render available models in a formatted table.

        Args:
            models: List of available model names
            current_model: The currently selected model name
        """
        table = Table(title="Available Models", show_header=True, header_style="bold magenta")
        table.add_column("Index", style="cyan", width=8)
        table.add_column("Model", style="green")
        table.add_column("Status", style="yellow", width=12)

        for i, model in enumerate(models):
            status = "✓ Active" if model == current_model else ""
            table.add_row(str(i), model, status)

        self.console.print(table)

    def render_history(self, messages: list) -> None:
        """Render conversation history in a formatted view.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
        """
        for i, msg in enumerate(messages):
            role = msg.get("role", "?")
            content = msg.get("content", "")[:100].replace("\n", " ")
            role_style = "cyan" if role == "assistant" else "blue" if role == "user" else "white"
            self.console.print(f"[bold {role_style}][{i}] {role}:[/bold {role_style}] {content}", highlight=False)

    def render_help(self) -> None:
        """Render the help/commands information."""
        commands = [
            ("/load <url>", "Load a YouTube video or webpage URL"),
            ("/model <index>", "List and choose an Ollama model"),
            ("/ctx <size>", "Set the context size (default: 32000)"),
            ("/subs", "Print the full loaded content (subtitles or webpage text)"),
            ("/summary", "Ask the model for a concise summary"),
            ("/hist", "Show the chat history"),
            ("/clear", "Clear the chat history (keeps loaded content)"),
            ("/reset", "Complete reset of the application"),
            ("/cls", "Clear the terminal screen"),
            ("/exit, /quit, /bye", "Quit the app"),
            ("/help", "Show this help message"),
        ]

        content = Text()
        for i, (cmd, desc) in enumerate(commands):
            if i > 0:
                content.append("\n")
            content.append(cmd.ljust(25, " "), style="bold cyan")
            content.append(f"  —  {desc}")

        content.append("\n\n")
        content.append("Just type a message to chat about the loaded content.", style="cyan")

        self.console.print(
            Panel(
                content,
                title="[bold green]Commands[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    def render_loading_message(self) -> None:
        """Render a "thinking" indicator."""
        self.console.print("[cyan]Assistant: Thinking...[/cyan]")

    def render_plain(self, text: str) -> None:
        """Render plain text without special formatting.

        Args:
            text: The text to render
        """
        self.console.print(text)
