from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_project_member
from src.domain.enums import TaskStatus
from src.domain.project import ProjectMember
from src.domain.task import Task
from src.repositories.task_repository import TaskRepository
from src.schemas.task import TaskCreate, TaskUpdate
from src.services.task_service import TaskService

router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])


def _build_service(session: AsyncSession) -> TaskService:
    return TaskService(TaskRepository(session))


@router.get("")
async def list_tasks(
    project_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
    status_filter: TaskStatus | None = Query(None, alias="status"),
) -> list[Task]:
    service = _build_service(session)
    return await service.get_tasks(project_id, member, status=status_filter)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: UUID,
    body: TaskCreate,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> Task:
    service = _build_service(session)
    return await service.create_task(
        title=body.title,
        project_id=project_id,
        member=member,
        description=body.description,
        priority=body.priority,
        assigned_to=body.assigned_to,
        due_date=body.due_date,
    )


@router.get("/{task_id}")
async def get_task(
    project_id: UUID,
    task_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> Task:
    service = _build_service(session)
    return await service.get_task(task_id, project_id, member)


@router.put("/{task_id}")
async def update_task(
    project_id: UUID,
    task_id: UUID,
    body: TaskUpdate,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> Task:
    service = _build_service(session)
    fields = body.model_dump(exclude_unset=True)
    return await service.update_task(task_id, project_id, member, **fields)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: UUID,
    task_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = _build_service(session)
    await service.delete_task(task_id, project_id, member)