"""Unit tests for ConfigService."""

from datetime import time

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.dtos.config import (
    CreateContentSourceRequest,
    UpdateDigestSettingsRequest,
    UpdateInterestKeywordsRequest,
)
from app.models.users import ContentSource, DigestConfiguration, InterestProfile, User
from app.services.config_service import ConfigService
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_get_user_config_success(async_session):
    """Test fetching complete user configuration successfully."""
    user = User(
        email="config@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.flush()

    profile = InterestProfile(
        config_id=config.id,
        keywords=["tech", "ai"],
        relevance_threshold=40,
        boost_factor=1.0,
    )
    async_session.add(profile)

    source = ContentSource(
        config_id=config.id,
        source_type="rss",
        source_url="https://example.com/feed",
        source_name="Example Feed",
        is_active=True,
    )
    async_session.add(source)
    await async_session.commit()

    service = ConfigService(async_session)
    complete_config_dto = await service.get_user_config(user.id)

    assert complete_config_dto.config.delivery_time == config.delivery_time
    assert len(complete_config_dto.sources) == 1
    assert complete_config_dto.sources[0].source_name == "Example Feed"
    assert complete_config_dto.interest_profile.keywords == ["tech", "ai"]


@pytest.mark.asyncio
async def test_get_user_config_not_found(async_session):
    """Test error when configuration not found."""
    service = ConfigService(async_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_user_config("nonexistent-user-id")

    assert exc_info.value.status_code == 404
    assert "configuration not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_digest_settings_success(async_session):
    """Test updating digest configuration settings."""
    user = User(
        email="update@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.commit()

    service = ConfigService(async_session)
    update_dto = UpdateDigestSettingsRequest(
        delivery_time=time(9, 30),
        summary_style="detailed",
        is_active=False,
    )
    config_dto = await service.update_digest_settings(user.id, update_dto)

    assert config_dto.delivery_time == time(9, 30)
    assert config_dto.summary_style == "detailed"
    assert config_dto.is_active is False


@pytest.mark.asyncio
async def test_update_digest_settings_not_found(async_session):
    """Test error when updating non-existent configuration."""
    service = ConfigService(async_session)
    update_dto = UpdateDigestSettingsRequest(
        delivery_time=time(9, 0),
        summary_style="brief",
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_digest_settings("nonexistent", update_dto)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_add_content_source_success(async_session):
    """Test adding new content source."""
    user = User(
        email="source@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.commit()

    service = ConfigService(async_session)
    create_dto = CreateContentSourceRequest(
        source_type="blog",
        source_url="https://blog.example.com",
        source_name="Example Blog",
    )
    source_dto = await service.add_content_source(user.id, create_dto)

    assert source_dto.source_type == "blog"
    assert source_dto.source_url == "https://blog.example.com/"
    assert source_dto.source_name == "Example Blog"
    assert source_dto.is_active is True


@pytest.mark.asyncio
async def test_add_content_source_config_not_found(async_session):
    """Test error when adding source to non-existent configuration."""
    service = ConfigService(async_session)
    create_dto = CreateContentSourceRequest(
        source_type="rss",
        source_url="https://example.com",
        source_name="Test",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.add_content_source("nonexistent", create_dto)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_remove_content_source_success(async_session):
    """Test removing content source."""
    user = User(
        email="remove@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.flush()

    source = ContentSource(
        config_id=config.id,
        source_type="rss",
        source_url="https://example.com/feed",
        source_name="Example Feed",
        is_active=True,
    )
    async_session.add(source)
    await async_session.commit()

    service = ConfigService(async_session)
    await service.remove_content_source(user.id, source.id)

    # Verify deletion

    stmt = select(ContentSource).where(ContentSource.id == source.id)
    result = await async_session.exec(stmt)
    deleted_source = result.one_or_none()

    assert deleted_source is None


@pytest.mark.asyncio
async def test_remove_content_source_not_found(async_session):
    """Test error when removing non-existent source."""
    user = User(
        email="notfound@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.commit()

    service = ConfigService(async_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.remove_content_source(user.id, "nonexistent-source-id")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_interest_keywords_success(async_session):
    """Test updating interest profile keywords."""
    user = User(
        email="keywords@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.flush()

    profile = InterestProfile(
        config_id=config.id,
        keywords=[],
        relevance_threshold=40,
        boost_factor=1.0,
    )
    async_session.add(profile)
    await async_session.commit()

    service = ConfigService(async_session)
    keywords_list = ["python", "javascript", "rust", "golang"]
    update_dto = UpdateInterestKeywordsRequest(keywords=keywords_list)
    profile_dto = await service.update_interest_keywords(user.id, update_dto)

    assert len(profile_dto.keywords) == 4
    assert "python" in profile_dto.keywords
    assert "javascript" in profile_dto.keywords
    assert "rust" in profile_dto.keywords
    assert "golang" in profile_dto.keywords


@pytest.mark.asyncio
async def test_update_interest_keywords_strips_whitespace(async_session):
    """Test that keyword parsing strips whitespace correctly."""
    user = User(
        email="strip@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.flush()

    profile = InterestProfile(
        config_id=config.id,
        keywords=[],
        relevance_threshold=40,
        boost_factor=1.0,
    )
    async_session.add(profile)
    await async_session.commit()

    service = ConfigService(async_session)
    keywords_str = "  python  ,  javascript  , , rust,  "
    keywords_list = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
    update_dto = UpdateInterestKeywordsRequest(keywords=keywords_list)
    profile_dto = await service.update_interest_keywords(user.id, update_dto)

    assert len(profile_dto.keywords) == 3
    assert profile_dto.keywords == ["python", "javascript", "rust"]


@pytest.mark.asyncio
async def test_update_interest_keywords_too_many(async_session):
    """Test error when exceeding 50 keyword limit."""
    user = User(
        email="limit@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.flush()

    profile = InterestProfile(
        config_id=config.id,
        keywords=[],
        relevance_threshold=40,
        boost_factor=1.0,
    )
    async_session.add(profile)
    await async_session.commit()

    # Generate 51 keywords
    keywords_list = [f"keyword{i}" for i in range(51)]

    service = ConfigService(async_session)
    update_dto = UpdateInterestKeywordsRequest(keywords=keywords_list)

    with pytest.raises(HTTPException) as exc_info:
        await service.update_interest_keywords(user.id, update_dto)

    assert exc_info.value.status_code == 400
    assert "50 keywords" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_interest_keywords_profile_not_found(async_session):
    """Test error when profile doesn't exist."""
    user = User(
        email="noprofile@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.flush()

    config = DigestConfiguration(
        user_id=user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    async_session.add(config)
    await async_session.commit()
    # Note: No profile created

    service = ConfigService(async_session)
    keywords_list = ["python", "rust"]
    update_dto = UpdateInterestKeywordsRequest(keywords=keywords_list)

    with pytest.raises(HTTPException) as exc_info:
        await service.update_interest_keywords(user.id, update_dto)

    assert exc_info.value.status_code == 404
    assert "profile not found" in exc_info.value.detail.lower()
