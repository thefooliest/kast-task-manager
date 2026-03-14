from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import ProjectRole
from src.domain.project import MemberDetail, Project, ProjectMember
from src.models.project import ProjectModel
from src.models.project_member import ProjectMemberModel
from src.models.user import UserModel


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            owner_id=model.owner_id,
            created_at=model.created_at,
        )

    def _member_to_domain(self, model: ProjectMemberModel) -> ProjectMember:
        return ProjectMember(
            project_id=model.project_id,
            user_id=model.user_id,
            role=ProjectRole(model.role),
            joined_at=model.joined_at,
        )

    async def get_by_id(self, project_id: UUID) -> Project | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_user_projects(self, user_id: UUID) -> list[Project]:
        result = await self._session.execute(
            select(ProjectModel)
            .join(
                ProjectMemberModel,
                ProjectMemberModel.project_id == ProjectModel.id,
            )
            .where(ProjectMemberModel.user_id == user_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def create(self, name: str, owner_id: UUID, description: str | None = None) -> Project:
        model = ProjectModel(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        self._session.add(model)
        await self._session.flush()

        # Add owner as a project member
        member = ProjectMemberModel(
            project_id=model.id,
            user_id=owner_id,
            role=ProjectRole.OWNER.value,
        )
        self._session.add(member)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_member(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        result = await self._session.execute(
            select(ProjectMemberModel).where(
                ProjectMemberModel.project_id == project_id,
                ProjectMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._member_to_domain(model) if model else None

    async def add_member(self, project_id: UUID, user_id: UUID, role: ProjectRole) -> ProjectMember:
        model = ProjectMemberModel(
            project_id=project_id,
            user_id=user_id,
            role=role.value,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._member_to_domain(model)

    async def get_members(self, project_id: UUID) -> list[ProjectMember]:
        result = await self._session.execute(
            select(ProjectMemberModel).where(
                ProjectMemberModel.project_id == project_id
            )
        )
        return [self._member_to_domain(m) for m in result.scalars().all()]

    async def get_members_with_details(self, project_id: UUID) -> list[MemberDetail]:
        result = await self._session.execute(
            select(ProjectMemberModel, UserModel)
            .join(UserModel, UserModel.id == ProjectMemberModel.user_id)
            .where(ProjectMemberModel.project_id == project_id)
        )
        return [
            MemberDetail(
                user_id=member.user_id,
                email=user.email,
                full_name=user.full_name,
                role=ProjectRole(member.role),
                joined_at=member.joined_at,
            )
            for member, user in result.all()
        ]