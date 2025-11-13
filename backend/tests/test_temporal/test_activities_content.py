"""Tests for content fetching activities."""

from datetime import time

import pytest
from sqlmodel import Session

from app.exceptions import ValidationError
from app.models.users import (
    ContentSource,
    DigestConfiguration,
    InterestProfile,
    User,
)
from app.temporal.activities import schemas as sc
from app.temporal.activities.content import ContentActivities


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user."""
    user = User(
        id="user_test_001",
        email="test@example.com",
        hashed_password="hashed_password",
        is_verified=True,
        timezone="UTC",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_digest_config(session: Session, test_user: User) -> DigestConfiguration:
    """Create a test digest configuration."""
    config = DigestConfiguration(
        id="config_test_001",
        user_id=test_user.id,
        delivery_time=time(hour=7, minute=0),
        summary_style="brief",
        is_active=True,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@pytest.fixture
def test_sources(session: Session, test_digest_config: DigestConfiguration) -> list[ContentSource]:
    """Create test content sources."""
    sources = [
        ContentSource(
            id="source_001",
            config_id=test_digest_config.id,
            source_type="rss",
            source_url="https://example.com/feed.xml",
            source_name="Example News",
            is_active=True,
        ),
        ContentSource(
            id="source_002",
            config_id=test_digest_config.id,
            source_type="rss",
            source_url="https://tech.example.com/feed.xml",
            source_name="Tech News",
            is_active=True,
        ),
    ]
    for source in sources:
        session.add(source)
    session.commit()
    for source in sources:
        session.refresh(source)
    return sources


@pytest.fixture
def test_interest_profile(session: Session, test_digest_config: DigestConfiguration) -> InterestProfile:
    """Create a test interest profile."""
    profile = InterestProfile(
        id="profile_test_001",
        config_id=test_digest_config.id,
        keywords=["AI", "machine learning", "python", "web development"],
        relevance_threshold=40,
        boost_factor=1.0,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@pytest.mark.asyncio
async def test_fetch_user_config_success(
    clear_async_db_cache,
    test_user: User,
    test_digest_config: DigestConfiguration,
    test_sources: list[ContentSource],
    test_interest_profile: InterestProfile,
):
    """Test successful fetch of user configuration."""
    activity = ContentActivities()

    result = await activity.fetch_user_config(sc.FetchUserConfigRequest(user_id=test_user.id))

    assert isinstance(result, sc.FetchUserConfigResult)
    assert result.user_config.user_id == test_user.id
    assert result.user_config.email == test_user.email
    assert result.user_config.timezone == "UTC"
    assert result.user_config.delivery_time == time(hour=7, minute=0)
    assert result.user_config.summary_style == "brief"
    assert result.user_config.is_active is True

    # Check sources
    assert result.sources_count == 2
    assert len(result.user_config.sources) == 2
    source_names = {s.source_name for s in result.user_config.sources}
    assert source_names == {"Example News", "Tech News"}

    # Check interest profile
    assert result.keywords_count == 4
    assert result.user_config.interest_profile.keywords == [
        "AI",
        "machine learning",
        "python",
        "web development",
    ]
    assert result.user_config.interest_profile.relevance_threshold == 40
    assert result.user_config.interest_profile.boost_factor == 1.0

    # Check timestamps
    assert result.start_timestamp is not None
    assert result.end_timestamp is not None
    assert result.end_timestamp >= result.start_timestamp


@pytest.mark.asyncio
async def test_fetch_user_config_user_not_found(clear_async_db_cache):
    """Test fetch_user_config when user does not exist."""
    activity = ContentActivities()

    with pytest.raises(ValidationError) as exc_info:
        await activity.fetch_user_config(sc.FetchUserConfigRequest(user_id="nonexistent_user"))

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_fetch_user_config_no_active_config(clear_async_db_cache, test_user: User, session: Session):
    """Test fetch_user_config when user has no active config."""
    # Create user but no active config
    activity = ContentActivities()

    with pytest.raises(ValidationError) as exc_info:
        await activity.fetch_user_config(sc.FetchUserConfigRequest(user_id=test_user.id))

    assert "No active digest config" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_user_config_no_interest_profile(
    clear_async_db_cache,
    test_user: User,
    test_digest_config: DigestConfiguration,
    test_sources: list[ContentSource],
):
    """Test fetch_user_config when user has no interest profile."""
    activity = ContentActivities()

    with pytest.raises(ValidationError) as exc_info:
        await activity.fetch_user_config(sc.FetchUserConfigRequest(user_id=test_user.id))

    assert "No interest profile" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_user_config_empty_sources(
    clear_async_db_cache,
    test_user: User,
    test_digest_config: DigestConfiguration,
    test_interest_profile: InterestProfile,
):
    """Test fetch_user_config with no active sources."""
    activity = ContentActivities()

    result = await activity.fetch_user_config(sc.FetchUserConfigRequest(user_id=test_user.id))

    assert result.sources_count == 0
    assert len(result.user_config.sources) == 0


@pytest.mark.asyncio
async def test_fetch_user_config_inactive_sources_filtered(
    clear_async_db_cache,
    session: Session,
    test_user: User,
    test_digest_config: DigestConfiguration,
    test_interest_profile: InterestProfile,
):
    """Test that inactive sources are filtered out."""
    # Add a source and make it inactive
    inactive_source = ContentSource(
        id="source_inactive",
        config_id=test_digest_config.id,
        source_type="rss",
        source_url="https://inactive.example.com/feed.xml",
        source_name="Inactive News",
        is_active=False,
    )
    session.add(inactive_source)
    session.commit()

    activity = ContentActivities()

    result = await activity.fetch_user_config(sc.FetchUserConfigRequest(user_id=test_user.id))

    # Only the two active sources should be returned
    assert result.sources_count == 0
    assert len(result.user_config.sources) == 0
