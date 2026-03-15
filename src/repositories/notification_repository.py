from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.notification import Notification
from src.models.notification import NotificationModel


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            user_id=model.user_id,
            project_id=model.project_id,
            task_id=model.task_id,
            message=model.message,
            is_read=model.is_read,
            created_at=model.created_at,
        )

    async def get_by_user(
        self, user_id: UUID, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        query = select(NotificationModel).where(
            NotificationModel.user_id == user_id
        )
        if unread_only:
            query = query.where(NotificationModel.is_read == False)
        query = query.order_by(NotificationModel.created_at.desc()).limit(limit)

        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_unread_count(self, user_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(NotificationModel).where(
                NotificationModel.user_id == user_id,
                NotificationModel.is_read == False,
            )
        )
        return result.scalar_one()

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        result = await self._session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id,
            )
            .values(is_read=True)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: UUID) -> int:
        result = await self._session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.user_id == user_id,
                NotificationModel.is_read == False,
            )
            .values(is_read=True)
        )
        await self._session.commit()
        return result.rowcount

    async def exists_for_task(self, task_id: UUID, user_id: UUID) -> bool:
        """Check if a notification already exists for this task+user (idempotency)."""
        result = await self._session.execute(
            select(func.count()).select_from(NotificationModel).where(
                NotificationModel.task_id == task_id,
                NotificationModel.user_id == user_id,
            )
        )
        return result.scalar_one() > 0

    async def create(
        self,
        user_id: UUID,
        project_id: UUID,
        task_id: UUID,
        message: str,
    ) -> Notification:
        model = NotificationModel(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            message=message,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)