from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class ActivityAction(str, Enum):
    PROJECT_CREATED = "project_created"
    MEMBER_ADDED = "member_added"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_DELETED = "task_deleted"
    COMMENT_ADDED = "comment_added"
    COMMENT_DELETED = "comment_deleted"


@dataclass
class Activity:
    id: UUID
    action: ActivityAction
    project_id: UUID
    user_id: UUID
    detail: str
    created_at: datetime


@dataclass
class ActivityDetail:
    """Activity enriched with actor info for API responses."""
    id: UUID
    action: ActivityAction
    project_id: UUID
    user_id: UUID
    actor_name: str
    detail: str
    created_at: datetime