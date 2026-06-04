from __future__ import annotations

from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from todoist_kanban_tui.api.models import BoardData, TodoistSection, TodoistTask
from todoist_kanban_tui.app import TodoistKanbanApp


def make_task(
    id: str = "1",
    content: str = "Task",
    description: str = "",
    section_id: str | None = None,
    priority: int = 1,
    labels: list[str] | None = None,
    due_date: date | None = None,
    children: list[TodoistTask] | None = None,
) -> TodoistTask:
    return TodoistTask(
        id=id,
        content=content,
        description=description,
        section_id=section_id,
        project_id="p1",
        priority=priority,
        labels=labels or [],
        due_date=due_date,
        due_string=None,
        is_recurring=False,
        order=int(id),
        parent_id=None,
        url=f"https://todoist.com/app/task/{id}",
        children=children or [],
    )


def make_board(
    sections: list[TodoistSection] | None = None,
    tasks_by_section: dict[str | None, list[TodoistTask]] | None = None,
) -> BoardData:
    if sections is None:
        sections = [
            TodoistSection(id="s1", name="Todo", order=1, project_id="p1"),
            TodoistSection(id="s2", name="Doing", order=2, project_id="p1"),
            TodoistSection(id="s3", name="Done", order=3, project_id="p1"),
        ]
    if tasks_by_section is None:
        tasks_by_section = {
            "s1": [
                make_task("1", "Write tests", "Detailed description\nLine two", section_id="s1", priority=4),
                make_task("2", "Fix bug", "", section_id="s1", priority=3),
                make_task("3", "Review PR", "Review notes here", section_id="s1"),
            ],
            "s2": [
                make_task("4", "Deploy v2", "Deploy to staging first", section_id="s2", priority=4),
                make_task("5", "Update docs", "", section_id="s2"),
            ],
            "s3": [
                make_task("6", "Setup CI", "CI pipeline configured", section_id="s3"),
            ],
        }
    return BoardData(
        project_name="Test Project",
        project_id="p1",
        sections=sections,
        tasks_by_section=tasks_by_section,
        fetched_at=datetime.now(),
    )


@pytest.fixture
def board():
    return make_board()


@pytest.fixture
def app(board):
    with patch("todoist_kanban_tui.app.RefreshServer") as mock_server:
        mock_server.return_value.start = AsyncMock()
        mock_server.return_value.stop = AsyncMock()

        app = TodoistKanbanApp(
            api_token="fake-token",
            project_id="p1",
            refresh_seconds=9999,
        )
        app.client.fetch_board = AsyncMock(return_value=board)
        app.client.move_task = AsyncMock(return_value=None)
        yield app
