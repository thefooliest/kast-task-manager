from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user, get_project_member
from src.domain.project import MemberDetail, Project, ProjectMember
from src.domain.user import User
from src.repositories.project_repository import ProjectRepository
from src.repositories.user_repository import UserRepository
from src.schemas.project import AddMemberRequest, ProjectCreate
from src.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _build_service(session: AsyncSession) -> ProjectService:
    return ProjectService(ProjectRepository(session))


@router.get("")
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Project]:
    service = _build_service(session)
    return await service.get_user_projects(current_user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Project:
    service = _build_service(session)
    return await service.create_project(
        name=body.name,
        owner_id=current_user.id,
        description=body.description,
    )


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> Project:
    service = _build_service(session)
    project = await service.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.get("/{project_id}/members")
async def list_members(
    project_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> list[MemberDetail]:
    service = _build_service(session)
    return await service.get_members_with_details(project_id)


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: UUID,
    body: AddMemberRequest,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> ProjectMember:
    service = _build_service(session)

    if not await service.is_owner(project_id, member.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can add members",
        )

    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing = await service.get_membership(project_id, user.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )

    return await service.add_member(project_id, user.id)