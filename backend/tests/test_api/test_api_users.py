"""Comprehensive tests for user management API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.users import ContentSource, User
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


# Digest Configuration Endpoint Tests
@pytest.mark.asyncio
async def test_get_digest_config_success(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test authenticated user can retrieve their digest configuration."""
    response = await async_client.get("/users/config", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["delivery_time"] == "07:00:00"
    assert data["summary_style"] == "brief"
    assert data["is_active"] is True
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source_name"] == "Example Feed"
    assert "technology" in data["interest_profile"]["keywords"]


@pytest.mark.asyncio
async def test_get_digest_config_unauthenticated(async_client, clear_async_db_cache):
    """Test unauthenticated config retrieval fails."""
    response = await async_client.get("/users/config")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_digest_config_success(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test authenticated user can update digest configuration."""
    response = await async_client.put(
        "/users/config",
        json={
            "delivery_time": "09:30:00",
            "summary_style": "detailed",
            "is_active": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "successfully" in data["message"].lower()
    assert data["config"]["delivery_time"] == "09:30:00"
    assert data["config"]["summary_style"] == "detailed"
    assert data["config"]["is_active"] is False


@pytest.mark.asyncio
async def test_update_digest_config_unauthenticated(async_client, clear_async_db_cache):
    """Test unauthenticated config update fails."""
    response = await async_client.put(
        "/users/config",
        json={
            "delivery_time": "10:00:00",
            "summary_style": "brief",
            "is_active": True,
        },
    )

    assert response.status_code == 403


# Content Source Endpoint Tests
@pytest.mark.asyncio
async def test_add_content_source_success(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test authenticated user can add a content source."""
    response = await async_client.post(
        "/users/sources",
        json={
            "source_type": "rss",
            "source_url": "https://news.ycombinator.com/rss",
            "source_name": "Hacker News",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "rss"
    assert data["source_url"] == "https://news.ycombinator.com/rss"
    assert data["source_name"] == "Hacker News"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_add_content_source_unauthenticated(async_client, clear_async_db_cache):
    """Test unauthenticated source addition fails."""
    response = await async_client.post(
        "/users/sources",
        json={
            "source_type": "rss",
            "source_url": "https://example.com/feed",
            "source_name": "Example",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_content_source_success(
    async_client,
    clear_async_db_cache,
    test_user_with_config: tuple,
    auth_headers: dict,
    session: Session,
):
    """Test authenticated user can delete their content source."""
    _, config = test_user_with_config

    # Get the source ID from the config
    stmt = select(ContentSource).where(ContentSource.config_id == config.id)
    result = session.exec(stmt)
    sources = result.all()
    assert len(sources) > 0
    source_id = sources[0].id

    response = await async_client.delete(f"/users/sources/{source_id}", headers=auth_headers)

    assert response.status_code == 200
    assert "removed successfully" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_delete_content_source_not_found(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test deleting non-existent source returns 404."""
    response = await async_client.delete("/users/sources/nonexistent_id_123", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_content_source_unauthenticated(async_client, clear_async_db_cache):
    """Test unauthenticated source deletion fails."""
    response = await async_client.delete("/users/sources/some_id")

    assert response.status_code == 403


# Interest Profile Endpoint Tests
@pytest.mark.asyncio
async def test_update_interest_profile_success(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test authenticated user can update interest profile keywords."""
    response = await async_client.put(
        "/users/interest-profile",
        json={"keywords": "python, machine learning, web development, startups"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "successfully" in data["message"].lower()
    assert "python" in data["keywords"]
    assert "machine learning" in data["keywords"]


@pytest.mark.asyncio
async def test_update_interest_profile_empty_keywords(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test updating interest profile with empty keywords."""
    response = await async_client.put("/users/interest-profile", json={"keywords": ""}, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["keywords"] == ""


@pytest.mark.asyncio
async def test_update_interest_profile_keyword_limit(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test updating interest profile enforces 50 keyword limit."""
    # Create 51 keywords
    keywords = ", ".join([f"keyword{i}" for i in range(51)])

    response = await async_client.put("/users/interest-profile", json={"keywords": keywords}, headers=auth_headers)

    assert response.status_code == 400
    assert "50" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_interest_profile_strips_whitespace(
    async_client, clear_async_db_cache, test_user_with_config: tuple, auth_headers: dict
):
    """Test keyword whitespace is properly stripped."""
    response = await async_client.put(
        "/users/interest-profile",
        json={"keywords": "  python  ,  ai  ,  data science  "},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # Keywords should be cleaned but order preserved
    assert "python" in data["keywords"]
    assert "ai" in data["keywords"]
    assert "data science" in data["keywords"]


@pytest.mark.asyncio
async def test_update_interest_profile_unauthenticated(async_client, clear_async_db_cache):
    """Test unauthenticated interest profile update fails."""
    response = await async_client.put("/users/interest-profile", json={"keywords": "technology, AI"})

    assert response.status_code == 403


# Integration Tests
@pytest.mark.asyncio
async def test_full_user_flow(async_client, clear_async_db_cache):
    """Test complete user flow: register → login → use authenticated endpoints."""
    # Step 1: Register
    register_response = await async_client.post(
        "/auth/register",
        json={
            "email": "flowtest@example.com",
            "password": "flowpassword123",
            "timezone": "UTC",
        },
    )
    assert register_response.status_code == 201

    # Step 2: Login
    login_response = await async_client.post(
        "/auth/login",
        json={
            "email": "flowtest@example.com",
            "password": "flowpassword123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Get profile
    profile_response = await async_client.get("/users/me", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "flowtest@example.com"

    # Step 4: Update timezone
    update_response = await async_client.put("/users/me", json={"timezone": "Europe/Paris"}, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["timezone"] == "Europe/Paris"

    # Step 5: Get config (should exist from registration)
    config_response = await async_client.get("/users/config", headers=headers)
    assert config_response.status_code == 200
    config_data = config_response.json()
    assert config_data["delivery_time"] == "07:00:00"
    assert config_data["summary_style"] == "brief"

    # Step 6: Add a content source
    source_response = await async_client.post(
        "/users/sources",
        json={
            "source_type": "rss",
            "source_url": "https://example.com/feed.xml",
            "source_name": "Test Feed",
        },
        headers=headers,
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    # Step 7: Update interest profile
    interest_response = await async_client.put(
        "/users/interest-profile",
        json={"keywords": "technology, programming"},
        headers=headers,
    )
    assert interest_response.status_code == 200

    # Step 8: Verify config includes new source and interests
    final_config = await async_client.get("/users/config", headers=headers)
    assert final_config.status_code == 200
    final_data = final_config.json()
    assert len(final_data["sources"]) == 1
    assert final_data["sources"][0]["source_name"] == "Test Feed"
    assert "technology" in final_data["interest_profile"]["keywords"]

    # Step 9: Delete the source
    delete_response = await async_client.delete(f"/users/sources/{source_id}", headers=headers)
    assert delete_response.status_code == 200
