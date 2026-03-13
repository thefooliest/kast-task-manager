from uuid import UUID

from src.domain.enums import ProjectRole
from src.domain.project import Project, ProjectMember
from src.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def get_user_projects(self, user_id: UUID) -> list[Project]:
        return await self._project_repo.get_user_projects(user_id)

    async def get_project(self, project_id: UUID) -> Project | None:
        return await self._project_repo.get_by_id(project_id)

    async def create_project(
        self, name: str, owner_id: UUID, description: str | None = None
    ) -> Project:
        return await self._project_repo.create(
            name=name, owner_id=owner_id, description=description
        )

    async def get_membership(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        """Returns the user's membership in a project, or None if not a member."""
        return await self._project_repo.get_member(project_id, user_id)

    async def is_owner(self, project_id: UUID, user_id: UUID) -> bool:
        member = await self._project_repo.get_member(project_id, user_id)
        return member is not None and member.role == ProjectRole.OWNER

    async def add_member(self, project_id: UUID, user_id: UUID) -> ProjectMember:
        return await self._project_repo.add_member(
            project_id=project_id, user_id=user_id, role=ProjectRole.MEMBER
        )

    async def get_members(self, project_id: UUID) -> list[ProjectMember]:
        return await self._project_repo.get_members(project_id)