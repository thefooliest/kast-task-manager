from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_project_member
from src.domain.comment import Comment, CommentDetail
from src.domain.project import ProjectMember
from src.repositories.comment_repository import CommentRepository
from src.repositories.task_repository import TaskRepository
from src.schemas.comment import CommentCreate
from src.services.comment_service import CommentService

router = APIRouter(
    prefix="/api/projects/{project_id}/tasks/{task_id}/comments",
    tags=["comments"],
)


def _build_service(session: AsyncSession) -> CommentService:
    return CommentService(CommentRepository(session), TaskRepository(session))


@router.get("")
async def list_comments(
    project_id: UUID,
    task_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> list[CommentDetail]:
    service = _build_service(session)
    return await service.get_comments(task_id, project_id, member)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_comment(
    project_id: UUID,
    task_id: UUID,
    body: CommentCreate,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> Comment:
    service = _build_service(session)
    return await service.create_comment(
        content=body.content,
        task_id=task_id,
        project_id=project_id,
        member=member,
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    project_id: UUID,
    task_id: UUID,
    comment_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = _build_service(session)
    await service.delete_comment(comment_id, project_id, member)