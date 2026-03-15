import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from src.core.scheduler import check_overdue_tasks
from src.models.task import TaskModel
from tests.conftest import async_session_test


@pytest.mark.asyncio
async def test_overdue_checker_creates_notification(
    client: AsyncClient, auth_headers, test_project, test_user, db_session
):
    user, _ = test_user

    # Create an overdue task directly in DB
    task = TaskModel(
        title="Overdue Task",
        status="todo",
        priority="high",
        project_id=test_project.id,
        created_by=user.id,
        assigned_to=user.id,
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(task)
    await db_session.commit()

    # Run the checker against test DB
    await check_overdue_tasks(session_factory=async_session_test)

    # Check notifications
    response = await client.get("/api/notifications", headers=auth_headers)
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) >= 1
    assert any("Overdue Task" in n["message"] for n in notifications)


@pytest.mark.asyncio
async def test_overdue_checker_is_idempotent(
    client: AsyncClient, auth_headers, test_project, test_user, db_session
):
    user, _ = test_user

    task = TaskModel(
        title="Idempotent Check",
        status="todo",
        priority="medium",
        project_id=test_project.id,
        created_by=user.id,
        assigned_to=user.id,
        due_date=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(task)
    await db_session.commit()

    # Run twice
    await check_overdue_tasks(session_factory=async_session_test)
    await check_overdue_tasks(session_factory=async_session_test)

    response = await client.get("/api/notifications", headers=auth_headers)
    notifications = response.json()
    overdue_notifs = [n for n in notifications if "Idempotent Check" in n["message"]]
    assert len(overdue_notifs) == 1


@pytest.mark.asyncio
async def test_overdue_checker_skips_done_tasks(
    client: AsyncClient, auth_headers, test_project, test_user, db_session
):
    user, _ = test_user

    task = TaskModel(
        title="Done But Overdue",
        status="done",
        priority="low",
        project_id=test_project.id,
        created_by=user.id,
        assigned_to=user.id,
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(task)
    await db_session.commit()

    await check_overdue_tasks(session_factory=async_session_test)

    response = await client.get("/api/notifications", headers=auth_headers)
    notifications = response.json()
    assert not any("Done But Overdue" in n["message"] for n in notifications)


@pytest.mark.asyncio
async def test_unread_count(
    client: AsyncClient, auth_headers, test_project, test_user, db_session
):
    user, _ = test_user

    task = TaskModel(
        title="Count Test",
        status="todo",
        priority="high",
        project_id=test_project.id,
        created_by=user.id,
        assigned_to=user.id,
        due_date=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(task)
    await db_session.commit()

    await check_overdue_tasks(session_factory=async_session_test)

    response = await client.get("/api/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["count"] >= 1


@pytest.mark.asyncio
async def test_mark_as_read(
    client: AsyncClient, auth_headers, test_project, test_user, db_session
):
    user, _ = test_user

    task = TaskModel(
        title="Read Test",
        status="todo",
        priority="high",
        project_id=test_project.id,
        created_by=user.id,
        assigned_to=user.id,
        due_date=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(task)
    await db_session.commit()

    await check_overdue_tasks(session_factory=async_session_test)

    # Get the notification
    list_resp = await client.get("/api/notifications", headers=auth_headers)
    notif_id = list_resp.json()[0]["id"]

    # Mark as read
    response = await client.put(
        f"/api/notifications/{notif_id}/read", headers=auth_headers
    )
    assert response.status_code == 200

    # Unread count should be 0
    count_resp = await client.get("/api/notifications/unread-count", headers=auth_headers)
    assert count_resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_as_read(
    client: AsyncClient, auth_headers, test_project, test_user, db_session
):
    user, _ = test_user

    for i in range(3):
        task = TaskModel(
            title=f"Bulk Read {i}",
            status="todo",
            priority="high",
            project_id=test_project.id,
            created_by=user.id,
            assigned_to=user.id,
            due_date=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(task)
    await db_session.commit()

    await check_overdue_tasks(session_factory=async_session_test)

    response = await client.put("/api/notifications/read-all", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["marked"] >= 3

    count_resp = await client.get("/api/notifications/unread-count", headers=auth_headers)
    assert count_resp.json()["count"] == 0