import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_activity_logged_on_task_create(
    client: AsyncClient, auth_headers, test_project
):
    # Create a task
    await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Logged Task"},
        headers=auth_headers,
    )

    # Check activity
    response = await client.get(
        f"/api/projects/{test_project.id}/activity",
        headers=auth_headers,
    )
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) >= 1
    assert any("Logged Task" in e["detail"] for e in entries)
    assert entries[0]["actor_name"] == "Test User"


@pytest.mark.asyncio
async def test_activity_logged_on_task_update(
    client: AsyncClient, auth_headers, test_project
):
    # Create then update
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Update Tracker"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    await client.put(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/projects/{test_project.id}/activity",
        headers=auth_headers,
    )
    entries = response.json()
    # Should have at least create + status change
    assert len(entries) >= 2
    assert any("status" in e["detail"] for e in entries)


@pytest.mark.asyncio
async def test_activity_logged_on_task_delete(
    client: AsyncClient, auth_headers, test_project
):
    create_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Delete Tracker"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    await client.delete(
        f"/api/projects/{test_project.id}/tasks/{task_id}",
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/projects/{test_project.id}/activity",
        headers=auth_headers,
    )
    entries = response.json()
    assert any("Deleted" in e["detail"] for e in entries)


@pytest.mark.asyncio
async def test_activity_logged_on_comment(
    client: AsyncClient, auth_headers, test_project
):
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Comment Tracker"},
        headers=auth_headers,
    )
    task_id = task_resp.json()["id"]

    await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "A tracked comment"},
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/projects/{test_project.id}/activity",
        headers=auth_headers,
    )
    entries = response.json()
    assert any(e["action"] == "comment_added" for e in entries)


@pytest.mark.asyncio
async def test_activity_respects_pagination(
    client: AsyncClient, auth_headers, test_project
):
    # Create several tasks
    for i in range(5):
        await client.post(
            f"/api/projects/{test_project.id}/tasks",
            json={"title": f"Task {i}"},
            headers=auth_headers,
        )

    response = await client.get(
        f"/api/projects/{test_project.id}/activity?limit=3",
        headers=auth_headers,
    )
    entries = response.json()
    assert len(entries) == 3


@pytest.mark.asyncio
async def test_activity_non_member_denied(
    client: AsyncClient, second_auth_headers, test_project
):
    response = await client.get(
        f"/api/projects/{test_project.id}/activity",
        headers=second_auth_headers,
    )
    assert response.status_code == 403