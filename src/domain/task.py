from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.enums import TaskPriority, TaskStatus


@dataclass
class Task:
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    project_id: UUID
    created_by: UUID
    assigned_to: UUID | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime