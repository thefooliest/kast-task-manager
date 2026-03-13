from datetime import datetime
from uuid import UUID

from src.domain.enums import ProjectRole, TaskPriority, TaskStatus
from src.domain.project import ProjectMember
from src.domain.task import Task
from src.repositories.task_repository import TaskRepository


class TaskServiceError(Exception):
    pass


class NotFoundError(TaskServiceError):
    pass


class PermissionDeniedError(TaskServiceError):
    pass


class TaskService:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    def _can_modify_task(self, task: Task, member: ProjectMember) -> bool:
        """Owner can modify any task. Members can only modify tasks they created or are assigned to."""
        if member.role == ProjectRole.OWNER:
            return True
        return task.created_by == member.user_id or task.assigned_to == member.user_id

    async def get_tasks(
        self,
        project_id: UUID,
        member: ProjectMember,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """All project members can see all tasks."""
        return await self._task_repo.get_by_project(project_id, status=status)

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