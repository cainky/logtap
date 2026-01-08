"""Files command for logtap CLI - list available log files."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def files(
    server: str = typer.Option(
        "http://localhost:8000",
        "--server",
        "-s",
        help="URL of the logtap server.",
        envvar="LOGTAP_SERVER",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for authentication.",
        envvar="LOGTAP_API_KEY",
    ),
    output: str = typer.Option(
        "pretty",
        "--output",
        "-o",
        help="Output format: pretty, json, plain.",
    ),
) -> None:
    """
    List available log files on the server.

    Example:
        logtap files
        logtap files --server http://myserver:8000
    """
    import httpx

    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{server}/files", headers=headers)

        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text)
            console.print(f"[bold red]Error:[/bold red] {error_detail}")
            raise typer.Exit(1)

        data = response.json()
        files_list = data.get("files", [])
        directory = data.get("directory", "")

        # Format output
        if output == "json":
            console.print_json(data=data)
        elif output == "plain":
            for f in files_list:
                console.print(f)
        else:
            # Pretty output with table
            if files_list:
                table = Table(title=f"Log files in {directory}")
                table.add_column("Filename", style="cyan")

                for f in files_list:
                    table.add_row(f)

                console.print(table)
                console.print(f"\n[dim]{len(files_list)} files found[/dim]")
            else:
                console.print(f"[dim]No log files found in {directory}[/dim]")

    except httpx.ConnectError:
        console.print(f"[bold red]Error:[/bold red] Could not connect to {server}")
        console.print("[dim]Is the logtap server running? Start it with 'logtap serve'[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
