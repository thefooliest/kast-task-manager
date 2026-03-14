from datetime import datetime
from uuid import UUID

from src.domain.enums import ProjectRole, TaskPriority, TaskStatus
from src.domain.project import ProjectMember
from src.domain.task import Task
from src.repositories.project_repository import ProjectRepository
from src.repositories.task_repository import TaskRepository


class TaskServiceError(Exception):
    pass


class NotFoundError(TaskServiceError):
    pass


class PermissionDeniedError(TaskServiceError):
    pass


class ValidationError(TaskServiceError):
    pass


class TaskService:
    def __init__(self, task_repo: TaskRepository, project_repo: ProjectRepository):
        self._task_repo = task_repo
        self._project_repo = project_repo

    def _can_modify_task(self, task: Task, member: ProjectMember) -> bool:
        """Owner can modify any task. Members can only modify tasks they created or are assigned to."""
        if member.role == ProjectRole.OWNER:
            return True
        return task.created_by == member.user_id or task.assigned_to == member.user_id

    async def _validate_assignee(self, project_id: UUID, assigned_to: UUID | None) -> None:
        """Verify the assigned user is a member of the project."""
        if assigned_to is None:
            return
        member = await self._project_repo.get_member(project_id, assigned_to)
        if member is None:
            raise ValidationError("Assigned user is not a member of this project")

    async def get_tasks(
        self,
        project_id: UUID,
        member: ProjectMember,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        """All project members can see all tasks. Returns (tasks, total_count)."""
        return await self._task_repo.get_by_project(
            project_id, status=status, limit=limit, offset=offset
        )

    async def get_task(
        self, task_id: UUID, project_id: UUID, member: ProjectMember
    ) -> Task:
        task = await self._task_repo.get_by_id(task_id)
        if task is None or task.project_id != project_id:
            raise NotFoundError("Task not found")
        return task

    async def create_task(
        self,
        title: str,
        project_id: UUID,
        member: ProjectMember,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_to: UUID | None = None,
        due_date: datetime | None = None,
    ) -> Task:
        """Any project member can create tasks."""
        await self._validate_assignee(project_id, assigned_to)
        return await self._task_repo.create(
            title=title,
            project_id=project_id,
            created_by=member.user_id,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            due_date=due_date,
        )

    async def update_task(
        self,
        task_id: UUID,
        project_id: UUID,
        member: ProjectMember,
        **fields,
    ) -> Task:
        task = await self._task_repo.get_by_id(task_id)
        if task is None or task.project_id != project_id:
            raise NotFoundError("Task not found")

        if not self._can_modify_task(task, member):
            raise PermissionDeniedError("You don't have permission to modify this task")

        if "assigned_to" in fields:
            await self._validate_assignee(project_id, fields["assigned_to"])

        updated = await self._task_repo.update(task_id, **fields)
        if updated is None:
            raise NotFoundError("Task not found")
        return updated

    async def delete_task(
        self, task_id: UUID, project_id: UUID, member: ProjectMember
    ) -> None:
        task = await self._task_repo.get_by_id(task_id)
        if task is None or task.project_id != project_id:
            raise NotFoundError("Task not found")

        if not self._can_modify_task(task, member):
            raise PermissionDeniedError("You don't have permission to delete this task")

        await self._task_repo.delete(task_id)