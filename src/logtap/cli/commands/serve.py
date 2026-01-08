"""Server command for logtap CLI."""

from typing import Optional

import typer
from rich.console import Console

console = Console()


def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind to.",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind to.",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for authentication. Can also be set via LOGTAP_API_KEY env var.",
        envvar="LOGTAP_API_KEY",
    ),
    log_dir: str = typer.Option(
        "/var/log",
        "--log-dir",
        "-d",
        help="Directory containing log files.",
        envvar="LOGTAP_LOG_DIRECTORY",
    ),
) -> None:
    """
    Start the logtap API server.

    Example:
        logtap serve
        logtap serve --port 9000
        logtap serve --api-key mysecretkey
    """
    import os

    import uvicorn

    # Set environment variables for the app
    os.environ["LOGTAP_HOST"] = host
    os.environ["LOGTAP_PORT"] = str(port)
    os.environ["LOGTAP_LOG_DIRECTORY"] = log_dir
    if api_key:
        os.environ["LOGTAP_API_KEY"] = api_key

    console.print("[bold green]Starting logtap server[/bold green]")
    console.print(f"  [dim]Host:[/dim] {host}")
    console.print(f"  [dim]Port:[/dim] {port}")
    console.print(f"  [dim]Log directory:[/dim] {log_dir}")
    console.print(f"  [dim]Auth:[/dim] {'enabled' if api_key else 'disabled'}")
    console.print()
    console.print(f"[dim]API docs available at[/dim] http://{host}:{port}/docs")
    console.print()

    uvicorn.run(
        "logtap.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )
