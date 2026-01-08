"""Tail command for logtap CLI - real-time log streaming."""

from typing import Optional

import typer
from rich.console import Console

console = Console()


def tail(
    filename: str = typer.Argument(
        "syslog",
        help="Name of the log file to tail.",
    ),
    server: str = typer.Option(
        "http://localhost:8000",
        "--server",
        "-s",
        help="URL of the logtap server.",
        envvar="LOGTAP_SERVER",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow log output (like tail -f). Requires WebSocket support.",
    ),
    lines: int = typer.Option(
        10,
        "--lines",
        "-n",
        help="Number of lines to show initially.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for authentication.",
        envvar="LOGTAP_API_KEY",
    ),
) -> None:
    """
    Tail a log file, optionally following new entries.

    Example:
        logtap tail syslog
        logtap tail auth.log -f
        logtap tail syslog --lines 100
    """
    import httpx

    # First, get initial lines
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    params = {
        "filename": filename,
        "limit": lines,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{server}/logs", params=params, headers=headers)

        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text)
            console.print(f"[bold red]Error:[/bold red] {error_detail}")
            raise typer.Exit(1)

        data = response.json()
        log_lines = data.get("lines", [])

        # Print initial lines
        for line in log_lines:
            console.print(line)

        if follow:
            console.print()
            console.print("[dim]Streaming new entries... (Ctrl+C to stop)[/dim]")
            console.print()

            # Stream new entries via WebSocket
            import asyncio

            async def stream_logs():
                import websockets

                ws_url = server.replace("http://", "ws://").replace("https://", "wss://")
                ws_url = f"{ws_url}/logs/stream?filename={filename}"

                extra_headers = {}
                if api_key:
                    extra_headers["X-API-Key"] = api_key

                try:
                    async with websockets.connect(ws_url, extra_headers=extra_headers) as ws:
                        async for message in ws:
                            console.print(message)
                except websockets.exceptions.InvalidStatusCode as e:
                    if e.status_code == 404:
                        console.print("[yellow]Streaming not available.[/yellow]")
                        console.print("[dim]Server may need updating.[/dim]")
                    else:
                        console.print(f"[red]WebSocket error: {e}[/red]")
                except Exception as e:
                    console.print(f"[red]Streaming error: {e}[/red]")

            try:
                asyncio.run(stream_logs())
            except KeyboardInterrupt:
                console.print("\n[dim]Stopped.[/dim]")

    except httpx.ConnectError:
        console.print(f"[bold red]Error:[/bold red] Could not connect to {server}")
        console.print("[dim]Is the logtap server running? Start it with 'logtap serve'[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
