"""Digest Configuration API endpoint tests."""

import pytest
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.users import ContentSource


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
