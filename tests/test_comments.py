import pytest
from httpx import AsyncClient

from src.domain.enums import ProjectRole
from src.models.project_member import ProjectMemberModel


@pytest.mark.asyncio
async def test_create_comment(client: AsyncClient, auth_headers, test_project):
    # Create a task first
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Task with comments"},
        headers=auth_headers,
    )
    task_id = task_resp.json()["id"]

    response = await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "This is a comment"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is a comment"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_comments(client: AsyncClient, auth_headers, test_project):
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Task for listing comments"},
        headers=auth_headers,
    )
    task_id = task_resp.json()["id"]

    # Create two comments
    await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "First comment"},
        headers=auth_headers,
    )
    await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "Second comment"},
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        headers=auth_headers,
    )
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) == 2
    assert comments[0]["author_name"] == "Test User"
    assert comments[0]["content"] == "First comment"


@pytest.mark.asyncio
async def test_delete_own_comment(client: AsyncClient, auth_headers, test_project):
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Task for delete test"},
        headers=auth_headers,
    )
    task_id = task_resp.json()["id"]

    comment_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "Delete me"},
        headers=auth_headers,
    )
    comment_id = comment_resp.json()["id"]

    response = await client.delete(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments/{comment_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify deleted
    list_resp = await client.get(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        headers=auth_headers,
    )
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_member_cannot_delete_others_comment(
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

    # Owner creates task and comment
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Owner's task"},
        headers=auth_headers,
    )
    task_id = task_resp.json()["id"]

    comment_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "Owner's comment"},
        headers=auth_headers,
    )
    comment_id = comment_resp.json()["id"]

    # Member tries to delete owner's comment — should fail
    response = await client.delete(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments/{comment_id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_delete_any_comment(
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

    # Member creates task and comment
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Member's task"},
        headers=second_auth_headers,
    )
    task_id = task_resp.json()["id"]

    comment_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "Member's comment"},
        headers=second_auth_headers,
    )
    comment_id = comment_resp.json()["id"]

    # Owner deletes member's comment — should succeed
    response = await client.delete(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments/{comment_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_non_member_cannot_comment(
    client: AsyncClient, second_auth_headers, test_project, auth_headers
):
    task_resp = await client.post(
        f"/api/projects/{test_project.id}/tasks",
        json={"title": "Protected task"},
        headers=auth_headers,
    )
    task_id = task_resp.json()["id"]

    # Non-member tries to comment
    response = await client.post(
        f"/api/projects/{test_project.id}/tasks/{task_id}/comments",
        json={"content": "Sneaky comment"},
        headers=second_auth_headers,
    )
    assert response.status_code == 403