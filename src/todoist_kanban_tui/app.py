from __future__ import annotations

import webbrowser
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Label
from textual import work

from .api.client import TodoistClient
from .api.models import BoardData
from .ipc.server import RefreshServer
from .widgets.kanban_board import KanbanBoard
from .widgets.section_column import SectionColumn
from .widgets.status_bar import StatusBar
from .widgets.task_card import TaskCard


class TodoistKanbanApp(App[None]):
    CSS_PATH = Path("assets/style.tcss")
    TITLE = "Todoist Kanban"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("o", "open_in_browser", "Open", show=False),
        Binding("d", "toggle_description", "Description", show=False),
        Binding("space", "toggle_lift", "Lift/Drop", show=True),
        Binding("escape", "cancel_lift", "Cancel", show=False),
        Binding("up", "navigate('up')", "Up", show=False),
        Binding("down", "navigate('down')", "Down", show=False),
        Binding("left", "navigate('left')", "Left", show=False),
        Binding("right", "navigate('right')", "Right", show=False),
        Binding("k", "navigate('up')", "Up", show=False),
        Binding("j", "navigate('down')", "Down", show=False),
        Binding("h", "navigate('left')", "Left", show=False),
        Binding("l", "navigate('right')", "Right", show=False),
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
        self._lifted_card: TaskCard | None = None
        self._original_section_id: str | None = None
        self._original_column: SectionColumn | None = None
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
        if self._lifted_card is not None:
            self._clear_lift_state()
        if data:
            header = self.query_one("#app-header", Label)
            header.update(f"📋 {data.project_name}")
            await self.query_one(KanbanBoard).update_board(data)

    def action_open_in_browser(self) -> None:
        if self._lifted_card is not None:
            return
        focused = self.focused
        if isinstance(focused, TaskCard):
            webbrowser.open(focused.task_data.url)

    def action_toggle_description(self) -> None:
        if self._lifted_card is not None:
            return
        focused = self.focused
        if isinstance(focused, TaskCard):
            focused.toggle_expanded()

    def action_toggle_lift(self) -> None:
        if self._lifted_card is not None:
            self._drop_card()
        else:
            focused = self.focused
            if isinstance(focused, TaskCard):
                self._lift_card(focused)

    def _lift_card(self, card: TaskCard) -> None:
        current_col = next(
            (a for a in card.ancestors_with_self if isinstance(a, SectionColumn)),
            None,
        )
        if current_col is None:
            return
        self._lifted_card = card
        self._original_section_id = card.task_data.section_id
        self._original_column = current_col
        card.add_class("lifted")
        current_col.add_class("drop-target")
        self.query_one(StatusBar).show_lift_mode(card.task_data.content)

    def _drop_card(self) -> None:
        card = self._lifted_card
        if card is None:
            return

        current_col = next(
            (a for a in card.ancestors_with_self if isinstance(a, SectionColumn)),
            None,
        )
        new_section_id = current_col._section.id if current_col and current_col._section else None
        old_section_id = self._original_section_id

        self._clear_lift_state()

        if new_section_id != old_section_id and self.board_data:
            card.task_data.section_id = new_section_id
            old_list = self.board_data.tasks_by_section.get(old_section_id, [])
            task_to_move = next((t for t in old_list if t.id == card.task_data.id), None)
            if task_to_move:
                old_list.remove(task_to_move)
                task_to_move.section_id = new_section_id
                new_list = self.board_data.tasks_by_section.setdefault(new_section_id, [])
                new_list.append(task_to_move)
            self._persist_move(card.task_data.id, new_section_id)

        card.focus()

    async def action_cancel_lift(self) -> None:
        if self._lifted_card is None:
            return
        card = self._lifted_card
        original_col = self._original_column

        current_col = next(
            (a for a in card.ancestors_with_self if isinstance(a, SectionColumn)),
            None,
        )

        if current_col is not original_col and original_col is not None:
            await self._move_card_widget(card, current_col, original_col)

        self._clear_lift_state()
        card.focus()

    def _clear_lift_state(self) -> None:
        if self._lifted_card:
            self._lifted_card.remove_class("lifted")
        for col in self.query("SectionColumn.drop-target"):
            col.remove_class("drop-target")
        self._lifted_card = None
        self._original_section_id = None
        self._original_column = None
        self.query_one(StatusBar).hide_lift_mode()

    @work(group="move", exclusive=True)
    async def _persist_move(self, task_id: str, section_id: str | None) -> None:
        if not self.client:
            return
        try:
            await self.client.move_task(task_id, section_id)
            section_name = "Unsectioned"
            if section_id:
                for s in (self.board_data.sections if self.board_data else []):
                    if s.id == section_id:
                        section_name = s.name
                        break
            self.notify(f"Moved to {section_name}", timeout=3)
        except Exception as e:
            self.notify(f"Move failed: {e}", severity="error", timeout=5)
            self.action_refresh()

    async def action_navigate(self, direction: str) -> None:
        if self._lifted_card is not None:
            if direction in ("left", "right"):
                await self._move_lifted_card(direction)
            return

        focused = self.focused
        if not isinstance(focused, TaskCard):
            columns = list(self.query(SectionColumn))
            if columns:
                first_cards = columns[0].query(TaskCard)
                if first_cards:
                    first_cards.first(TaskCard).focus()
            return

        current_col = next((a for a in focused.ancestors_with_self if isinstance(a, SectionColumn)), None)
        if current_col is None:
            return
        cards_in_col = list(current_col.query(TaskCard))
        card_idx = cards_in_col.index(focused)

        if direction in ("up", "down"):
            delta = -1 if direction == "up" else 1
            new_idx = (card_idx + delta) % len(cards_in_col)
            target = cards_in_col[new_idx]
        else:
            columns = list(self.query(SectionColumn))
            if not columns:
                return
            col_idx = columns.index(current_col)
            delta = -1 if direction == "left" else 1
            new_col_idx = (col_idx + delta) % len(columns)
            new_col = columns[new_col_idx]
            new_cards = list(new_col.query(TaskCard))
            if not new_cards:
                return
            target = new_cards[min(card_idx, len(new_cards) - 1)]

        target.focus()
        target.scroll_visible()

    async def _move_lifted_card(self, direction: str) -> None:
        card = self._lifted_card
        if card is None:
            return

        current_col = next(
            (a for a in card.ancestors_with_self if isinstance(a, SectionColumn)),
            None,
        )
        if current_col is None:
            return

        columns = list(self.query(SectionColumn))
        col_idx = columns.index(current_col)
        delta = -1 if direction == "left" else 1
        new_col_idx = col_idx + delta

        if new_col_idx < 0 or new_col_idx >= len(columns):
            return

        target_col = columns[new_col_idx]

        await self._move_card_widget(card, current_col, target_col)

        current_col.remove_class("drop-target")
        target_col.add_class("drop-target")

        card.focus()
        card.scroll_visible()

    async def _move_card_widget(
        self, card: TaskCard, from_col: SectionColumn, to_col: SectionColumn
    ) -> None:
        to_scroll = to_col.query_one(".column-scroll", VerticalScroll)

        await card.remove()
        await to_scroll.mount(card)

        from_col.update_header_count()
        to_col.update_header_count()

    def on_click(self, event: Click) -> None:
        if self._lifted_card is not None:
            return
        widget = self.screen.get_widget_at(event.screen_x, event.screen_y)[0]
        while widget is not None:
            if isinstance(widget, TaskCard):
                widget.toggle_expanded()
                return
            widget = widget.parent

    def action_show_help(self) -> None:
        self.notify(
            "Space=Lift/Drop  Esc=Cancel move\n"
            "r=Refresh  q=Quit  o=Open in browser\n"
            "↑↓/jk=Cards  ←→/hl=Columns  d=Description  ?=Help",
            title="Keybindings",
            timeout=8,
        )
