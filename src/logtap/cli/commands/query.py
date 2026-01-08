"""Query command for logtap CLI."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def query(
    filename: str = typer.Argument(
        "syslog",
        help="Name of the log file to query.",
    ),
    server: str = typer.Option(
        "http://localhost:8000",
        "--server",
        "-s",
        help="URL of the logtap server.",
        envvar="LOGTAP_SERVER",
    ),
    term: Optional[str] = typer.Option(
        None,
        "--term",
        "-t",
        help="Substring to search for.",
    ),
    regex: Optional[str] = typer.Option(
        None,
        "--regex",
        "-r",
        help="Regex pattern to match.",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-n",
        help="Number of lines to return.",
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
    case_sensitive: bool = typer.Option(
        True,
        "--case-sensitive/--ignore-case",
        "-c/-i",
        help="Whether search is case-sensitive.",
    ),
) -> None:
    """
    Query logs from a logtap server.

    Example:
        logtap query syslog
        logtap query auth.log --term "Failed password"
        logtap query syslog --regex "error.*connection" --limit 100
    """

    import httpx

    # Build request
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    params = {
        "filename": filename,
        "limit": limit,
        "case_sensitive": case_sensitive,
    }
    if term:
        params["term"] = term
    if regex:
        params["regex"] = regex

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{server}/logs", params=params, headers=headers)

        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text)
            console.print(f"[bold red]Error:[/bold red] {error_detail}")
            raise typer.Exit(1)

        data = response.json()
        lines = data.get("lines", [])
        count = data.get("count", len(lines))

        # Format output
        if output == "json":
            console.print_json(data=data)
        elif output == "plain":
            for line in lines:
                console.print(line)
        else:
            # Pretty output with panel
            if lines:
                content = "\n".join(lines)
                panel = Panel(
                    content,
                    title=f"[bold blue]{filename}[/bold blue]",
                    subtitle=f"[dim]{count} lines[/dim]",
                    border_style="blue",
                )
                console.print(panel)
            else:
                console.print(f"[dim]No matching lines found in {filename}[/dim]")

    except httpx.ConnectError:
        console.print(f"[bold red]Error:[/bold red] Could not connect to {server}")
        console.print("[dim]Is the logtap server running? Start it with 'logtap serve'[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
