from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.domain.notification import Notification
from src.domain.user import User
from src.repositories.notification_repository import NotificationRepository

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _build_repo(session: AsyncSession) -> NotificationRepository:
    return NotificationRepository(session)


@router.get("")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
) -> list[Notification]:
    repo = _build_repo(session)
    return await repo.get_by_user(current_user.id, unread_only=unread_only, limit=limit)


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    repo = _build_repo(session)
    count = await repo.get_unread_count(current_user.id)
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    repo = _build_repo(session)
    success = await repo.mark_as_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return {"status": "ok"}


@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    repo = _build_repo(session)
    count = await repo.mark_all_as_read(current_user.id)
    return {"marked": count}