import pytest
from httpx import AsyncClient



async def test_login_success(client: AsyncClient, test_user):
    user, password = test_user
    response = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name



async def test_login_wrong_password(client: AsyncClient, test_user):
    user, _ = test_user
    response = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401



async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password"},
    )
    assert response.status_code == 401



async def test_login_invalid_email_format(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": "password"},
    )
    assert response.status_code == 422



async def test_protected_endpoint_without_token(client: AsyncClient):
    response = await client.get("/api/projects")
    assert response.status_code == 401



async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/projects",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401