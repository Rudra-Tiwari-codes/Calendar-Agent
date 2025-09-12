from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from rich.text import Text
from typing import Any

console = Console()

def format_message(role: str, message: str) -> None:
    if role == 'user':
        panel = Panel(
            message,
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
    elif role == 'assistant':
        panel = Panel(
            message,
            title="[bold green]Assistant[/bold green]",
            border_style="green",
            padding=(0, 1)
        )
    console.print(panel)


def format_error(error: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {error}")


def format_tool_call(tool_name: str, arguments: dict) -> None:
    table = Table(title=f"🔧 Calling tool: {tool_name}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    for key, value in arguments.items():
        table.add_row(key, str(value))

    console.print(table)


def format_welcome() -> None:
    welcome_text = Text.from_markup(
        """[bold blue]🤖 CLI Chatbot[/bold blue]

        Connected to OpenAI with tool support!
        Type your message or 'quit' to exit."""
    )

    panel = Panel(
        welcome_text,
        title="[bold green]Welcome[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


def format_tool_result(tool_name: str, result: Any) -> None:
    panel = Panel(
        str(result),
        title=f"[bold cyan]🔧 Tool Result: {tool_name}[/bold cyan]",
        border_style="cyan",
        padding=(0, 1)
    )
    console.print(panel)