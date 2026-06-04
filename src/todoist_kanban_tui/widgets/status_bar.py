from __future__ import annotations

from datetime import datetime

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    project_name = reactive("")
    last_refresh = reactive("")
    is_refreshing = reactive(False)
    lift_mode_text = reactive("")

    def __init__(self) -> None:
        super().__init__(markup=False)

    def render(self) -> str:
        if self.lift_mode_text:
            return f" MOVING: {self.lift_mode_text}  │  ←→ Move  Space Drop  Esc Cancel"
        spinner = " ⟳ " if self.is_refreshing else ""
        refresh_text = f"Last refresh: {self.last_refresh}" if self.last_refresh else "Loading..."
        return f"{spinner}{self.project_name}  │  {refresh_text}  │  [r] Refresh  [q] Quit  [?] Help"

    def update_status(self, project_name: str, refreshed_at: datetime | None, refreshing: bool = False) -> None:
        self.project_name = project_name
        self.is_refreshing = refreshing
        if refreshed_at:
            self.last_refresh = refreshed_at.strftime("%H:%M:%S")

    def show_lift_mode(self, task_content: str) -> None:
        self.lift_mode_text = task_content[:40]

    def hide_lift_mode(self) -> None:
        self.lift_mode_text = ""
