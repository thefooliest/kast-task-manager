from uuid import UUID

from src.domain.activity import ActivityAction, ActivityDetail
from src.repositories.activity_repository import ActivityRepository


class ActivityService:
    def __init__(self, activity_repo: ActivityRepository):
        self._repo = activity_repo

    async def log(
        self,
        action: ActivityAction,
        project_id: UUID,
        user_id: UUID,
        detail: str,
    ) -> None:
        await self._repo.create(
            action=action,
            project_id=project_id,
            user_id=user_id,
            detail=detail,
        )

    async def get_project_activity(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ActivityDetail]:
        return await self._repo.get_by_project(project_id, limit=limit, offset=offset)