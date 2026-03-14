from uuid import UUID

from src.domain.activity import ActivityAction
from src.domain.enums import ProjectRole
from src.domain.project import MemberDetail, Project, ProjectMember
from src.repositories.project_repository import ProjectRepository
from src.services.activity_service import ActivityService


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        activity_service: ActivityService | None = None,
    ):
        self._project_repo = project_repo
        self._activity = activity_service

    async def _log(self, action: ActivityAction, project_id: UUID, user_id: UUID, detail: str):
        if self._activity:
            await self._activity.log(action, project_id, user_id, detail)

    async def get_user_projects(self, user_id: UUID) -> list[Project]:
        return await self._project_repo.get_user_projects(user_id)

    async def get_project(self, project_id: UUID) -> Project | None:
        return await self._project_repo.get_by_id(project_id)

    async def create_project(
        self, name: str, owner_id: UUID, description: str | None = None
    ) -> Project:
        project = await self._project_repo.create(
            name=name, owner_id=owner_id, description=description
        )
        await self._log(ActivityAction.PROJECT_CREATED, project.id, owner_id, f'Created project "{name}"')
        return project

    async def get_membership(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        return await self._project_repo.get_member(project_id, user_id)

    async def is_owner(self, project_id: UUID, user_id: UUID) -> bool:
        member = await self._project_repo.get_member(project_id, user_id)
        return member is not None and member.role == ProjectRole.OWNER

    async def add_member(self, project_id: UUID, user_id: UUID, added_by: UUID) -> ProjectMember:
        member = await self._project_repo.add_member(
            project_id=project_id, user_id=user_id, role=ProjectRole.MEMBER
        )
        await self._log(ActivityAction.MEMBER_ADDED, project_id, added_by, "Added a new member")
        return member

    async def get_members(self, project_id: UUID) -> list[ProjectMember]:
        return await self._project_repo.get_members(project_id)

    async def get_members_with_details(self, project_id: UUID) -> list[MemberDetail]:
        return await self._project_repo.get_members_with_details(project_id)