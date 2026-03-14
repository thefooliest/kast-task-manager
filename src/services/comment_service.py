from uuid import UUID

from src.domain.activity import ActivityAction
from src.domain.comment import Comment, CommentDetail
from src.domain.enums import ProjectRole
from src.domain.project import ProjectMember
from src.repositories.comment_repository import CommentRepository
from src.repositories.task_repository import TaskRepository
from src.services.activity_service import ActivityService
from src.services.task_service import NotFoundError, PermissionDeniedError


class CommentService:
    def __init__(
        self,
        comment_repo: CommentRepository,
        task_repo: TaskRepository,
        activity_service: ActivityService | None = None,
    ):
        self._comment_repo = comment_repo
        self._task_repo = task_repo
        self._activity = activity_service

    async def _verify_task_in_project(self, task_id: UUID, project_id: UUID) -> str:
        """Returns task title for logging, raises if not found."""
        task = await self._task_repo.get_by_id(task_id)
        if task is None or task.project_id != project_id:
            raise NotFoundError("Task not found")
        return task.title

    async def get_comments(
        self, task_id: UUID, project_id: UUID, member: ProjectMember
    ) -> list[CommentDetail]:
        await self._verify_task_in_project(task_id, project_id)
        return await self._comment_repo.get_by_task(task_id)

    async def create_comment(
        self,
        content: str,
        task_id: UUID,
        project_id: UUID,
        member: ProjectMember,
    ) -> Comment:
        """Any project member can comment on any task."""
        task_title = await self._verify_task_in_project(task_id, project_id)
        comment = await self._comment_repo.create(
            content=content, task_id=task_id, user_id=member.user_id
        )
        if self._activity:
            await self._activity.log(
                ActivityAction.COMMENT_ADDED, project_id, member.user_id,
                f'Commented on "{task_title}"',
            )
        return comment

    async def delete_comment(
        self,
        comment_id: UUID,
        project_id: UUID,
        member: ProjectMember,
    ) -> None:
        """Only the comment author or the project owner can delete a comment."""
        comment = await self._comment_repo.get_by_id(comment_id)
        if comment is None:
            raise NotFoundError("Comment not found")

        is_author = comment.user_id == member.user_id
        is_owner = member.role == ProjectRole.OWNER

        if not is_author and not is_owner:
            raise PermissionDeniedError("You don't have permission to delete this comment")

        await self._comment_repo.delete(comment_id)
        if self._activity:
            await self._activity.log(
                ActivityAction.COMMENT_DELETED, project_id, member.user_id,
                "Deleted a comment",
            )