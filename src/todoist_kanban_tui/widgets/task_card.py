from __future__ import annotations

from datetime import date

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

from ..api.models import TodoistTask

PRIORITY_DOTS = {4: ("🔴", "priority-4"), 3: ("🟡", "priority-3"), 2: ("🔵", "priority-2")}


class TaskCard(Static, can_focus=True):
    expanded = reactive(False)

    def __init__(self, task: TodoistTask) -> None:
        super().__init__()
        self.task_data = task
        self._is_overdue = bool(task.due_date and task.due_date < date.today())
        priority_class = PRIORITY_DOTS.get(task.priority, (None, None))[1]
        if priority_class:
            self.add_class(priority_class)
        if self._is_overdue:
            self.add_class("overdue")

    def render(self) -> Text:
        task = self.task_data
        lines: list[str] = []

        dot = PRIORITY_DOTS.get(task.priority, (None, None))[0]
        prefix = f"{dot} " if dot else ""
        lines.append(f"{prefix}{task.content}")

        meta_parts: list[str] = []
        if task.due_date:
            due_str = task.due_date.strftime("%b %d")
            if self._is_overdue:
                due_str = f"⚠ {due_str}"
            meta_parts.append(f"📅 {due_str}")
        if task.is_recurring and task.due_string:
            meta_parts.append(f"🔁 {task.due_string}")
        if task.labels:
            meta_parts.append(f"🏷 {', '.join(task.labels[:3])}")
        if meta_parts:
            lines.append("  ".join(meta_parts))

        if task.children:
            for i, child in enumerate(task.children):
                connector = "└─" if i == len(task.children) - 1 else "├─"
                child_dot = PRIORITY_DOTS.get(child.priority, (None, None))[0]
                child_prefix = f"{child_dot} " if child_dot else ""
                lines.append(f"  {connector} {child_prefix}{child.content}")

        if self.expanded:
            lines.append("")
            if task.description:
                desc_lines = task.description.strip().split("\n")[:6]
                for dl in desc_lines:
                    lines.append(f"  {dl[:60]}")
            else:
                lines.append("  No description")

        return Text("\n".join(lines))

    def toggle_expanded(self) -> None:
        self.expanded = not self.expanded

    def watch_expanded(self) -> None:
        self.refresh(layout=True)
