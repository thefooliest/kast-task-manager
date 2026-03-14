from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.comment import Comment, CommentDetail
from src.domain.enums import ProjectRole
from src.models.comment import CommentModel
from src.models.user import UserModel


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, model: CommentModel) -> Comment:
        return Comment(
            id=model.id,
            content=model.content,
            task_id=model.task_id,
            user_id=model.user_id,
            created_at=model.created_at,
        )

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_task(self, task_id: UUID) -> list[CommentDetail]:
        result = await self._session.execute(
            select(CommentModel, UserModel)
            .join(UserModel, UserModel.id == CommentModel.user_id)
            .where(CommentModel.task_id == task_id)
            .order_by(CommentModel.created_at.asc())
        )
        return [
            CommentDetail(
                id=comment.id,
                content=comment.content,
                task_id=comment.task_id,
                user_id=comment.user_id,
                author_name=user.full_name,
                author_email=user.email,
                created_at=comment.created_at,
            )
            for comment, user in result.all()
        ]

    async def count_by_task(self, task_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(CommentModel).where(
                CommentModel.task_id == task_id
            )
        )
        return result.scalar_one()

    async def create(self, content: str, task_id: UUID, user_id: UUID) -> Comment:
        model = CommentModel(
            content=content,
            task_id=task_id,
            user_id=user_id,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, comment_id: UUID) -> bool:
        result = await self._session.execute(
            delete(CommentModel).where(CommentModel.id == comment_id)
        )
        await self._session.commit()
        return result.rowcount > 0