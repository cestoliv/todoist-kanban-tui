from __future__ import annotations

import atexit
import asyncio
import os
import signal
from typing import TYPE_CHECKING

from ..constants import APP_DIR, PID_PATH, SOCKET_PATH

if TYPE_CHECKING:
    from ..app import TodoistKanbanApp


def _cleanup_files() -> None:
    for path in (SOCKET_PATH, PID_PATH):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


class RefreshServer:
    def __init__(self, app: TodoistKanbanApp) -> None:
        self._app = app
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        _cleanup_files()
        PID_PATH.write_text(str(os.getpid()))
        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(SOCKET_PATH),
        )
        atexit.register(_cleanup_files)
        for sig in (signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, lambda *_: _cleanup_files())

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            data = await asyncio.wait_for(reader.read(100), timeout=5)
            command = data.decode().strip()
            if command == "refresh":
                self._app.action_refresh()
                writer.write(b"ok\n")
            else:
                writer.write(b"unknown\n")
            await writer.drain()
        finally:
            writer.close()

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        _cleanup_files()
