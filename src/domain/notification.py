from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Notification:
    id: UUID
    user_id: UUID
    project_id: UUID
    task_id: UUID
    message: str
    is_read: bool
    created_at: datetime