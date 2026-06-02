from __future__ import annotations

from textual.containers import HorizontalScroll
from textual.widgets import Static

from ..api.models import BoardData
from .section_column import SectionColumn


class KanbanBoard(HorizontalScroll):
    async def update_board(self, data: BoardData) -> None:
        await self.remove_children()

        unsectioned = data.tasks_by_section.get(None, [])
        columns: list[SectionColumn] = []

        if unsectioned:
            columns.append(SectionColumn(None, unsectioned))

        for section in data.sections:
            tasks = data.tasks_by_section.get(section.id, [])
            columns.append(SectionColumn(section, tasks))

        if not columns:
            await self.mount(Static("No sections or tasks found in this project.", id="empty-board"))
            return

        await self.mount(*columns)

        n = len(columns)
        width_pct = max(22, 100 / min(n, 5))
        for col in self.query(SectionColumn):
            col.styles.width = f"{width_pct:.0f}%"
            col.styles.min_width = 28
