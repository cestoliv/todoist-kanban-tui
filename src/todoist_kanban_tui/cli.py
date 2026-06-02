from __future__ import annotations

import asyncio
import os
import sys

import click

from .constants import DEFAULT_REFRESH_SECONDS, SOCKET_PATH


@click.group(invoke_without_command=True)
@click.option("--project-id", envvar="TODOIST_PROJECT_ID", default=None, help="Todoist project ID")
@click.option("--refresh", "refresh_seconds", default=DEFAULT_REFRESH_SECONDS, help="Auto-refresh interval in seconds")
@click.pass_context
def cli(ctx: click.Context, project_id: str | None, refresh_seconds: int) -> None:
    if ctx.invoked_subcommand is not None:
        return

    api_token = os.environ.get("TODOIST_API_TOKEN")
    if not api_token:
        click.echo("Error: TODOIST_API_TOKEN environment variable is required.", err=True)
        sys.exit(1)

    from .app import TodoistKanbanApp

    app = TodoistKanbanApp(api_token, project_id, refresh_seconds)
    app.run()


@cli.command("refresh")
def refresh_command() -> None:
    """Signal a running TUI to refresh its data."""
    if not SOCKET_PATH.exists():
        click.echo("No running TUI found (socket not found).", err=True)
        sys.exit(1)

    try:
        result = asyncio.run(_send_refresh())
        click.echo(result)
    except Exception as e:
        click.echo(f"Failed to signal refresh: {e}", err=True)
        sys.exit(1)


async def _send_refresh() -> str:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_unix_connection(str(SOCKET_PATH)),
            timeout=3,
        )
    except (asyncio.TimeoutError, ConnectionRefusedError, FileNotFoundError):
        return "error: TUI not responding (stale socket?)"
    try:
        writer.write(b"refresh\n")
        await writer.drain()
        response = await asyncio.wait_for(reader.read(100), timeout=3)
        return response.decode().strip()
    finally:
        writer.close()
        await writer.wait_closed()
