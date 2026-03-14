from datetime import datetime
from uuid import UUID

from src.domain.activity import ActivityAction
from src.domain.enums import ProjectRole, TaskPriority, TaskStatus
from src.domain.project import ProjectMember
from src.domain.task import Task
from src.repositories.project_repository import ProjectRepository
from src.repositories.task_repository import TaskRepository
from src.services.activity_service import ActivityService


class TaskServiceError(Exception):
    pass


class NotFoundError(TaskServiceError):
    pass


class PermissionDeniedError(TaskServiceError):
    pass


class ValidationError(TaskServiceError):
    pass


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        activity_service: ActivityService | None = None,
    ):
        self._task_repo = task_repo
        self._project_repo = project_repo
        self._activity = activity_service

    async def _log(self, action: ActivityAction, project_id: UUID, user_id: UUID, detail: str):
        if self._activity:
            await self._activity.log(action, project_id, user_id, detail)

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
        task = await self._task_repo.create(
            title=title,
            project_id=project_id,
            created_by=member.user_id,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            due_date=due_date,
        )
        await self._log(ActivityAction.TASK_CREATED, project_id, member.user_id, f'Created task "{title}"')
        return task

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

        # Build meaningful detail message
        details = []
        if "status" in fields and fields["status"] != task.status:
            old = task.status.value if isinstance(task.status, TaskStatus) else task.status
            new = fields["status"].value if isinstance(fields["status"], TaskStatus) else fields["status"]
            details.append(f"status: {old} → {new}")
        if "assigned_to" in fields and fields["assigned_to"] != task.assigned_to:
            details.append("reassigned")
        if "title" in fields and fields["title"] != task.title:
            details.append(f'renamed to "{fields["title"]}"')

        updated = await self._task_repo.update(task_id, **fields)
        if updated is None:
            raise NotFoundError("Task not found")

        action = ActivityAction.TASK_STATUS_CHANGED if "status" in fields else ActivityAction.TASK_UPDATED
        detail_str = f'Updated task "{task.title}"'
        if details:
            detail_str += f" ({', '.join(details)})"
        await self._log(action, project_id, member.user_id, detail_str)

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
        await self._log(ActivityAction.TASK_DELETED, project_id, member.user_id, f'Deleted task "{task.title}"')