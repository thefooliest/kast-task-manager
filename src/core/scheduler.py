"""
Background scheduler that periodically checks for overdue tasks
and creates notifications for assigned users.

Runs as an asyncio task within the FastAPI lifespan.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session
from src.models.task import TaskModel
from src.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 300  # 5 minutes


async def check_overdue_tasks(session_factory=None):
    """
    Finds overdue tasks (due_date < now, status != done) and creates
    one notification per task per user. Idempotent — skips tasks that
    already have a notification for the target user.

    Args:
        session_factory: Optional async session factory. Defaults to production session.
    """
    factory = session_factory or async_session
    async with factory() as session:
        try:
            now = datetime.now(timezone.utc)

            result = await session.execute(
                select(TaskModel).where(
                    TaskModel.due_date < now,
                    TaskModel.status != "done",
                    TaskModel.due_date.isnot(None),
                )
            )
            overdue_tasks = result.scalars().all()

            if not overdue_tasks:
                return

            repo = NotificationRepository(session)
            created = 0

            for task in overdue_tasks:
                # Notify the assigned user, or the creator if unassigned
                target_user = task.assigned_to or task.created_by

                # Idempotency check — one notification per task per user
                already_notified = await repo.exists_for_task(task.id, target_user)
                if already_notified:
                    continue

                await repo.create(
                    user_id=target_user,
                    project_id=task.project_id,
                    task_id=task.id,
                    message=f'Task "{task.title}" is overdue',
                )
                created += 1

            if created > 0:
                logger.info(f"Created {created} overdue notification(s)")

        except Exception:
            logger.exception("Error checking overdue tasks")


async def overdue_checker_loop():
    """Runs check_overdue_tasks on a loop. Designed to be started as an asyncio task."""
    logger.info(f"Overdue checker started (interval: {CHECK_INTERVAL_SECONDS}s)")
    while True:
        await check_overdue_tasks()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)