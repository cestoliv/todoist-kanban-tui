from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Label, OptionList
from textual.widgets.option_list import Option


class ProjectPicker(Screen[str]):
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, projects: list[tuple[str, str]]) -> None:
        super().__init__()
        self._projects = projects

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Select a Todoist project:", id="picker-title")
        yield OptionList(
            *[Option(name, id=pid) for pid, name in self._projects],
            id="project-list",
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)
