import pytest
from httpx import AsyncClient

from src.domain.enums import ProjectRole
from src.models.project_member import ProjectMemberModel


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers, test_project):
    response = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Test Task", "description": "A test task", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "todo"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_headers, test_project):
    # Create a task first
    await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Task 1"},
        headers=auth_headers,
    )
    response = await client.get(
        f"/api/projects/{test_project.id}/tasks",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["tasks"]) >= 1


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(
    client: AsyncClient, auth_headers, test_project
):
    # Create tasks with different statuses
    await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Todo Task"},
        headers=auth_headers,
    )
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Done Task"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]
    await client.put(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        json={"status": "done"},
        headers=auth_headers,
    )

    # Filter by status
    response = await client.get(
        f"/api/projects/{test_project.id}/tasks?status=done",
        headers=auth_headers,
    )
    assert response.status_code == 200
    tasks = response.json()["tasks"]
    assert all(t["status"] == "done" for t in tasks)


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, auth_headers, test_project):
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Get Me"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers, test_project):
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Update Me"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        json={"title": "Updated", "status": "in_progress"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers, test_project):
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Delete Me"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    get_resp = await client.get(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_member_can_see_all_tasks(
    client: AsyncClient,
    auth_headers,
    second_auth_headers,
    test_project,
    second_user,
    db_session,
):
    # Add second_user as member
    user, _ = second_user
    member = ProjectMemberModel(
        project_id=test_project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER.value,
    )
    db_session.add(member)
    await db_session.commit()

    # Owner creates a task
    await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Owner Task"},
        headers=auth_headers,
    )

    # Member can see it
    response = await client.get(
        f"/api/projects/{test_project.id}/tasks",
        headers=second_auth_headers,
    )
    assert response.status_code == 200
    assert any(t["title"] == "Owner Task" for t in response.json()["tasks"])


@pytest.mark.asyncio
async def test_member_cannot_modify_others_task(
    client: AsyncClient,
    auth_headers,
    second_auth_headers,
    test_project,
    second_user,
    db_session,
):
    # Add second_user as member
    user, _ = second_user
    member = ProjectMemberModel(
        project_id=test_project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER.value,
    )
    db_session.add(member)
    await db_session.commit()

    # Owner creates a task
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Owner Only"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    # Member tries to update — should fail
    response = await client.put(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        json={"title": "Hacked"},
        headers=second_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_modify_any_task(
    client: AsyncClient,
    auth_headers,
    second_auth_headers,
    test_project,
    second_user,
    db_session,
):
    # Add second_user as member
    user, _ = second_user
    member = ProjectMemberModel(
        project_id=test_project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER.value,
    )
    db_session.add(member)
    await db_session.commit()

    # Member creates a task
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Member Task"},
        headers=second_auth_headers,
    )
    task_id = create_resp.json()["id"]

    # Owner can update it
    response = await client.put(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        json={"status": "done"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "done"


@pytest.mark.asyncio
async def test_non_member_cannot_access_tasks(
    client: AsyncClient, second_auth_headers, test_project
):
    response = await client.get(
        f"/api/projects/{test_project.id}/tasks",
        headers=second_auth_headers,
    )
    assert response.status_code == 403