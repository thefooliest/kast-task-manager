from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_project_member
from src.domain.activity import ActivityDetail
from src.domain.project import ProjectMember
from src.repositories.activity_repository import ActivityRepository
from src.services.activity_service import ActivityService

router = APIRouter(prefix="/api/projects/{project_id}/activity", tags=["activity"])


def _build_service(session: AsyncSession) -> ActivityService:
    return ActivityService(ActivityRepository(session))


@router.get("")
async def list_activity(
    project_id: UUID,
    member: ProjectMember = Depends(get_project_member),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ActivityDetail]:
    service = _build_service(session)
    return await service.get_project_activity(project_id, limit=limit, offset=offset)