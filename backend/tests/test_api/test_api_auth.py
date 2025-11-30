"""Authentication API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.users import User
from app.utils.auth import get_password_hash


# Authentication Endpoint Tests
def test_register_user_success(client: TestClient):
    """Test successful user registration with default config creation."""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["timezone"] == "America/New_York"
    assert data["is_verified"] is False
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_user_duplicate_email(async_client, clear_async_db_cache, test_user: User):
    """Test registration fails with duplicate email."""
    response = await async_client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpassword123",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_register_user_short_password(client: TestClient):
    """Test registration fails with password shorter than 8 characters."""
    response = client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 422


def test_register_user_invalid_timezone(client: TestClient):
    """Test registration fails with invalid timezone."""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "timezone": "Invalid/Timezone",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "timezone" in str(data).lower()
    assert "invalid" in str(data).lower()


@pytest.mark.asyncio
async def test_login_success(async_client, clear_async_db_cache, test_user: User):
    """Test successful login returns JWT token."""
    response = await async_client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_invalid_email(client: TestClient):
    """Test login fails with non-existent email."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword",
        },
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_invalid_password(async_client, clear_async_db_cache, test_user: User):
    """Test login fails with incorrect password."""
    response = await async_client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_inactive_user(async_client, clear_async_db_cache, session: Session):
    """Test login fails for inactive user account."""
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=False,
    )
    session.add(inactive_user)
    session.commit()

    response = await async_client.post(
        "/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()
