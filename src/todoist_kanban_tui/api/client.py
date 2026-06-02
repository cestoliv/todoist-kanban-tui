from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.models import Task

from .models import BoardData, TodoistSection, TodoistTask


def _parse_task(task: Task) -> TodoistTask:
    due_date = None
    due_string = None
    is_recurring = False
    if task.due:
        try:
            raw_date = task.due.date
            if isinstance(raw_date, date):
                due_date = raw_date
            elif isinstance(raw_date, str):
                due_date = date.fromisoformat(raw_date)
        except (ValueError, AttributeError):
            pass
        due_string = getattr(task.due, "string", None)
        is_recurring = getattr(task.due, "is_recurring", False)

    return TodoistTask(
        id=task.id,
        content=task.content,
        description=task.description or "",
        section_id=task.section_id or None,
        project_id=task.project_id,
        priority=task.priority,
        labels=list(task.labels) if task.labels else [],
        due_date=due_date,
        due_string=due_string,
        is_recurring=is_recurring,
        order=task.order,
        parent_id=task.parent_id or None,
        url=task.url,
    )


def _nest_tasks(flat_tasks: list[TodoistTask]) -> list[TodoistTask]:
    by_id: dict[str, TodoistTask] = {t.id: t for t in flat_tasks}
    roots: list[TodoistTask] = []
    for task in flat_tasks:
        if task.parent_id and task.parent_id in by_id:
            by_id[task.parent_id].children.append(task)
        else:
            roots.append(task)
    for task in by_id.values():
        task.children.sort(key=lambda t: t.order)
    return sorted(roots, key=lambda t: t.order)


class TodoistClient:
    def __init__(self, api_token: str, project_id: str):
        self._token = api_token
        self._project_id = project_id

    async def fetch_board(self) -> BoardData:
        async with TodoistAPIAsync(self._token) as api:
            project = await api.get_project(self._project_id)

            raw_sections: list = []
            async for page in await api.get_sections(project_id=self._project_id):
                raw_sections.extend(page)

            raw_tasks: list = []
            async for page in await api.get_tasks(project_id=self._project_id):
                raw_tasks.extend(page)

        sections = [
            TodoistSection(
                id=s.id,
                name=s.name,
                order=s.order,
                project_id=s.project_id,
            )
            for s in raw_sections
        ]
        sections.sort(key=lambda s: s.order)

        parsed_tasks = [_parse_task(t) for t in raw_tasks]

        tasks_by_section: dict[str | None, list[TodoistTask]] = defaultdict(list)
        for task in parsed_tasks:
            tasks_by_section[task.section_id].append(task)

        for section_id in tasks_by_section:
            tasks_by_section[section_id] = _nest_tasks(tasks_by_section[section_id])

        return BoardData(
            project_name=project.name,
            project_id=project.id,
            sections=sections,
            tasks_by_section=dict(tasks_by_section),
            fetched_at=datetime.now(),
        )

    async def fetch_projects(self) -> list[tuple[str, str]]:
        async with TodoistAPIAsync(self._token) as api:
            result: list[tuple[str, str]] = []
            async for page in await api.get_projects():
                for p in page:
                    result.append((p.id, p.name))
        return result
