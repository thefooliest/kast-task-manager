from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.activity import Activity, ActivityAction, ActivityDetail
from src.models.activity import ActivityModel
from src.models.user import UserModel


class ActivityRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        action: ActivityAction,
        project_id: UUID,
        user_id: UUID,
        detail: str,
    ) -> Activity:
        model = ActivityModel(
            action=action.value,
            project_id=project_id,
            user_id=user_id,
            detail=detail,
        )
        self._session.add(model)
        await self._session.commit()
        return Activity(
            id=model.id,
            action=ActivityAction(model.action),
            project_id=model.project_id,
            user_id=model.user_id,
            detail=model.detail,
            created_at=model.created_at,
        )

    async def get_by_project(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ActivityDetail]:
        result = await self._session.execute(
            select(ActivityModel, UserModel)
            .join(UserModel, UserModel.id == ActivityModel.user_id)
            .where(ActivityModel.project_id == project_id)
            .order_by(ActivityModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [
            ActivityDetail(
                id=activity.id,
                action=ActivityAction(activity.action),
                project_id=activity.project_id,
                user_id=activity.user_id,
                actor_name=user.full_name,
                detail=activity.detail,
                created_at=activity.created_at,
            )
            for activity, user in result.all()
        ]