from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class TodoistTask:
    id: str
    content: str
    description: str
    section_id: str | None
    project_id: str
    priority: int
    labels: list[str]
    due_date: date | None
    due_string: str | None
    is_recurring: bool
    order: int
    parent_id: str | None
    url: str
    children: list[TodoistTask] = field(default_factory=list)


@dataclass
class TodoistSection:
    id: str
    name: str
    order: int
    project_id: str


@dataclass
class BoardData:
    project_name: str
    project_id: str
    sections: list[TodoistSection]
    tasks_by_section: dict[str | None, list[TodoistTask]]
    fetched_at: datetime
