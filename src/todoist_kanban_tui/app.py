from __future__ import annotations

import webbrowser
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Label
from textual import work

from .api.client import TodoistClient
from .api.models import BoardData
from .ipc.server import RefreshServer
from .widgets.kanban_board import KanbanBoard
from .widgets.status_bar import StatusBar
from .widgets.task_card import TaskCard


class TodoistKanbanApp(App[None]):
    CSS_PATH = Path("assets/style.tcss")
    TITLE = "Todoist Kanban"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("o", "open_in_browser", "Open", show=False),
        Binding("question_mark", "show_help", "Help"),
    ]

    board_data: reactive[BoardData | None] = reactive(None, init=False)
    last_refresh: reactive[datetime | None] = reactive(None, init=False)

    def __init__(
        self,
        api_token: str,
        project_id: str | None,
        refresh_seconds: int = 300,
    ) -> None:
        super().__init__()
        self._api_token = api_token
        self._project_id = project_id
        self.client: TodoistClient | None = None
        self.refresh_server = RefreshServer(self)
        self._refresh_seconds = refresh_seconds
        if project_id:
            self.client = TodoistClient(api_token, project_id)

    def compose(self) -> ComposeResult:
        yield Label("Todoist Kanban", id="app-header")
        yield KanbanBoard()
        yield StatusBar()

    async def on_mount(self) -> None:
        self.theme = "dracula"
        await self.refresh_server.start()
        if self._project_id:
            self._start_board()
        else:
            self._show_picker()

    def _start_board(self) -> None:
        self.action_refresh()
        self.set_interval(self._refresh_seconds, self.action_refresh)

    @work(group="picker", exclusive=True)
    async def _show_picker(self) -> None:
        from .widgets.project_picker import ProjectPicker

        tmp_client = TodoistClient(self._api_token, "")
        projects = await tmp_client.fetch_projects()
        if not projects:
            self.notify("No projects found", severity="error")
            return

        def on_pick(project_id: str | None) -> None:
            if project_id:
                self._project_id = project_id
                self.client = TodoistClient(self._api_token, project_id)
                self._start_board()

        self.push_screen(ProjectPicker(projects), on_pick)

    async def on_unmount(self) -> None:
        await self.refresh_server.stop()

    @work(group="refresh", exclusive=True)
    async def action_refresh(self) -> None:
        if not self.client:
            return
        status_bar = self.query_one(StatusBar)
        project_name = self.board_data.project_name if self.board_data else ""
        status_bar.update_status(project_name, self.last_refresh, refreshing=True)

        try:
            data = await self.client.fetch_board()
            self.board_data = data
            self.last_refresh = datetime.now()
        except Exception as e:
            self.notify(f"Refresh failed: {e}", severity="error", timeout=5)
        finally:
            name = self.board_data.project_name if self.board_data else ""
            status_bar.update_status(name, self.last_refresh, refreshing=False)

    async def watch_board_data(self, data: BoardData | None) -> None:
        if data:
            header = self.query_one("#app-header", Label)
            header.update(f"📋 {data.project_name}")
            await self.query_one(KanbanBoard).update_board(data)

    def action_open_in_browser(self) -> None:
        focused = self.focused
        if isinstance(focused, TaskCard):
            webbrowser.open(focused.task_data.url)

    def action_show_help(self) -> None:
        self.notify(
            "r=Refresh  q=Quit  o=Open in browser\n"
            "h/l=Columns  j/k=Cards  ?=Help",
            title="Keybindings",
            timeout=8,
        )
