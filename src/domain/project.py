from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.enums import ProjectRole


@dataclass
class ProjectMember:
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    joined_at: datetime


@dataclass
class Project:
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    created_at: datetime