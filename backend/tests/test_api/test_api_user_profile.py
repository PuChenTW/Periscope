"""User Profile API endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from app.models.users import User


# User Profile Endpoint Tests
@pytest.mark.asyncio
async def test_get_user_profile_authenticated(async_client, clear_async_db_cache, test_user: User, auth_headers: dict):
    """Test authenticated user can retrieve their profile."""
    response = await async_client.get("/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["timezone"] == test_user.timezone
    assert data["is_verified"] == test_user.is_verified
    assert data["is_active"] == test_user.is_active


def test_get_user_profile_unauthenticated(client: TestClient):
    """Test unauthenticated request to get profile fails."""
    response = client.get("/users/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_profile_invalid_token(async_client, clear_async_db_cache):
    """Test invalid token fails authentication."""
    response = await async_client.get("/users/me", headers={"Authorization": "Bearer invalid_token_here"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile_timezone(async_client, clear_async_db_cache, test_user: User, auth_headers: dict):
    """Test authenticated user can update their timezone."""
    response = await async_client.put("/users/me", json={"timezone": "Europe/London"}, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "Europe/London"
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_user_profile_unauthenticated(async_client, clear_async_db_cache):
    """Test unauthenticated update fails."""
    response = await async_client.put("/users/me", json={"timezone": "Asia/Tokyo"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_profile_invalid_timezone(
    async_client, clear_async_db_cache, test_user: User, auth_headers: dict
):
    """Test user profile update fails with invalid timezone."""
    response = await async_client.put("/users/me", json={"timezone": "NotA/RealTimezone"}, headers=auth_headers)

    assert response.status_code == 422
    data = response.json()
    assert "timezone" in str(data).lower()
    assert "invalid" in str(data).lower()
