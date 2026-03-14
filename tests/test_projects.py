import pytest
from httpx import AsyncClient



async def test_create_project(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/projects",
        json={"name": "New Project", "description": "A new project"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert data["description"] == "A new project"
    assert "id" in data



async def test_list_projects(client: AsyncClient, auth_headers, test_project):
    response = await client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["name"] == "Test Project" for p in data)



async def test_get_project(client: AsyncClient, auth_headers, test_project):
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"



async def test_get_project_non_member(
    client: AsyncClient, second_auth_headers, test_project
):
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 403



async def test_add_member(
    client: AsyncClient, auth_headers, test_project, second_user
):
    user, _ = second_user
    response = await client.post(
        f"/api/projects/{test_project.id}/members",
        json={"email": user.email},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "member"



async def test_add_member_non_owner(
    client: AsyncClient, auth_headers, second_auth_headers, test_project, second_user, db_session
):
    # First add second_user as member
    from src.domain.enums import ProjectRole
    from src.models.project_member import ProjectMemberModel

    user, _ = second_user
    member = ProjectMemberModel(
        project_id=test_project.id,
        user_id=user.id,
        role=ProjectRole.MEMBER.value,
    )
    db_session.add(member)
    await db_session.commit()

    # Now second_user (member) tries to add someone — should fail
    response = await client.post(
        f"/api/projects/{test_project.id}/members",
        json={"email": "nobody@example.com"},
        headers=second_auth_headers,
    )
    assert response.status_code == 403



async def test_add_duplicate_member(
    client: AsyncClient, auth_headers, test_project, test_user
):
    user, _ = test_user
    response = await client.post(
        f"/api/projects/{test_project.id}/members",
        json={"email": user.email},
        headers=auth_headers,
    )
    assert response.status_code == 409