from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label

from ..api.models import TodoistSection, TodoistTask
from .task_card import TaskCard


class SectionColumn(Vertical):
    def __init__(
        self,
        section: TodoistSection | None,
        tasks: list[TodoistTask],
    ) -> None:
        section_id = section.id if section else "none"
        super().__init__(id=f"section_{section_id}")
        self._section = section
        self._tasks = tasks

    def compose(self) -> ComposeResult:
        name = self._section.name if self._section else "Unsectioned"
        yield Label(f" {name} ({len(self._tasks)}) ", classes="column-header")
        with VerticalScroll(classes="column-scroll"):
            for task in self._tasks:
                yield TaskCard(task)

    def update_header_count(self) -> None:
        name = self._section.name if self._section else "Unsectioned"
        count = len(list(self.query(TaskCard)))
        self.query_one(".column-header", Label).update(f" {name} ({count}) ")
