from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Comment:
    id: UUID
    content: str
    task_id: UUID
    user_id: UUID
    created_at: datetime


@dataclass
class CommentDetail:
    """Comment enriched with author info — used for API responses."""
    id: UUID
    content: str
    task_id: UUID
    user_id: UUID
    author_name: str
    author_email: str
    created_at: datetime