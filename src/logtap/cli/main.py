"""Main CLI application for logtap."""

import typer

from logtap import __version__
from logtap.cli.commands import files, query, serve, tail

app = typer.Typer(
    name="logtap",
    help="A CLI-first log access tool for Unix systems. Remote log file access without SSH.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"logtap {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    logtap - Remote log file access without SSH.

    Start a server with 'logtap serve' or query a remote server with 'logtap query'.
    """
    pass


# Add commands
app.command()(serve.serve)
app.command()(query.query)
app.command()(tail.tail)
app.command()(files.files)


if __name__ == "__main__":
    app()
