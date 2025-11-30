"""Tests for content fetching activities."""

from datetime import UTC, datetime, time
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import HttpUrl
from sqlmodel import Session

from app.exceptions import ValidationError
from app.models.users import (
    ContentSource,
    DigestConfiguration,
    InterestProfile,
    User,
)
from app.processors.fetchers.base import Article, FetchResult, SourceInfo
from app.processors.fetchers.exceptions import FetchTimeoutError, InvalidUrlError
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


# ============================================================================
# Tests for fetch_sources_parallel
# ============================================================================


@pytest.fixture
def sample_articles() -> list[Article]:
    """Create sample articles for testing."""
    return [
        Article(
            title="Test Article 1",
            url=HttpUrl("https://example.com/article1"),
            content="This is test article 1 content.",
            published_at=datetime.now(UTC),
            fetch_timestamp=datetime.now(UTC),
        ),
        Article(
            title="Test Article 2",
            url=HttpUrl("https://example.com/article2"),
            content="This is test article 2 content.",
            published_at=datetime.now(UTC),
            fetch_timestamp=datetime.now(UTC),
        ),
    ]


@pytest.fixture
def mock_source_configs() -> list[sc.ContentSourceConfig]:
    """Create mock source configurations."""
    return [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Example Feed 1",
            is_active=True,
        ),
        sc.ContentSourceConfig(
            id="source_002",
            source_type="rss",
            source_url="https://example.com/feed2.xml",
            source_name="Example Feed 2",
            is_active=True,
        ),
    ]


@pytest.mark.asyncio
async def test_fetch_sources_parallel_success(sample_articles):
    """Test successful parallel fetch from multiple sources."""
    fetch_result_1 = FetchResult(
        source_info=SourceInfo(title="Feed 1", url=HttpUrl("https://example.com/feed1.xml")),
        articles=sample_articles[:1],
        fetch_timestamp=datetime.now(UTC),
        success=True,
    )
    fetch_result_2 = FetchResult(
        source_info=SourceInfo(title="Feed 2", url=HttpUrl("https://example.com/feed2.xml")),
        articles=sample_articles[1:],
        fetch_timestamp=datetime.now(UTC),
        success=True,
    )

    # Mock the fetcher
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch_content = AsyncMock(side_effect=[fetch_result_1, fetch_result_2])

    sources = [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Feed 1",
            is_active=True,
        ),
        sc.ContentSourceConfig(
            id="source_002",
            source_type="rss",
            source_url="https://example.com/feed2.xml",
            source_name="Feed 2",
            is_active=True,
        ),
    ]

    with patch("app.temporal.activities.content.create_fetcher", return_value=mock_fetcher):
        activity = ContentActivities()
        result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=sources))

    assert isinstance(result, sc.FetchSourcesParallelResult)
    assert result.total_sources == 2
    assert result.successful_sources == 2
    assert result.failed_sources == 0
    assert result.total_articles == 2
    assert len(result.articles) == 2
    assert len(result.fetch_errors) == 0
    assert result.start_timestamp is not None
    assert result.end_timestamp is not None
    assert result.end_timestamp >= result.start_timestamp


@pytest.mark.asyncio
async def test_fetch_sources_parallel_partial_failure(sample_articles):
    """Test parallel fetch with some sources failing."""
    fetch_result_success = FetchResult(
        source_info=SourceInfo(title="Feed 1", url=HttpUrl("https://example.com/feed1.xml")),
        articles=sample_articles,
        fetch_timestamp=datetime.now(UTC),
        success=True,
    )
    fetch_result_failure = FetchResult(
        source_info=SourceInfo(title="Feed 2", url=HttpUrl("https://example.com/feed2.xml")),
        articles=[],
        fetch_timestamp=datetime.now(UTC),
        success=False,
        error_message="Connection timeout",
    )

    mock_fetcher = AsyncMock()
    mock_fetcher.fetch_content = AsyncMock(side_effect=[fetch_result_success, fetch_result_failure])

    sources = [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Feed 1",
            is_active=True,
        ),
        sc.ContentSourceConfig(
            id="source_002",
            source_type="rss",
            source_url="https://example.com/feed2.xml",
            source_name="Feed 2",
            is_active=True,
        ),
    ]

    with patch("app.temporal.activities.content.create_fetcher", return_value=mock_fetcher):
        activity = ContentActivities()
        result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=sources))

    assert result.total_sources == 2
    assert result.successful_sources == 1
    assert result.failed_sources == 1
    assert result.total_articles == 2
    assert len(result.articles) == 2
    assert len(result.fetch_errors) == 1
    assert "source_002" in result.fetch_errors
    assert "Connection timeout" in result.fetch_errors["source_002"]


@pytest.mark.asyncio
async def test_fetch_sources_parallel_exception_handling():
    """Test that exceptions during fetch are handled gracefully."""
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch_content = AsyncMock(side_effect=FetchTimeoutError("Request timed out"))

    sources = [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Feed 1",
            is_active=True,
        ),
    ]

    with patch("app.temporal.activities.content.create_fetcher", return_value=mock_fetcher):
        activity = ContentActivities()
        result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=sources))

    # Should not raise, but record the error
    assert result.total_sources == 1
    assert result.successful_sources == 0
    assert result.failed_sources == 1
    assert result.total_articles == 0
    assert len(result.articles) == 0
    assert "source_001" in result.fetch_errors


@pytest.mark.asyncio
async def test_fetch_sources_parallel_empty_sources():
    """Test fetch with empty sources list."""
    activity = ContentActivities()
    result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=[]))

    assert result.total_sources == 0
    assert result.successful_sources == 0
    assert result.failed_sources == 0
    assert result.total_articles == 0
    assert len(result.articles) == 0
    assert len(result.fetch_errors) == 0


@pytest.mark.asyncio
async def test_fetch_sources_parallel_inactive_sources_filtered():
    """Test that inactive sources are filtered out."""
    sources = [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Feed 1",
            is_active=True,
        ),
        sc.ContentSourceConfig(
            id="source_002",
            source_type="rss",
            source_url="https://example.com/feed2.xml",
            source_name="Feed 2",
            is_active=False,  # Inactive
        ),
    ]

    fetch_result = FetchResult(
        source_info=SourceInfo(title="Feed 1", url=HttpUrl("https://example.com/feed1.xml")),
        articles=[],
        fetch_timestamp=datetime.now(UTC),
        success=True,
    )

    mock_fetcher = AsyncMock()
    mock_fetcher.fetch_content = AsyncMock(return_value=fetch_result)

    with patch("app.temporal.activities.content.create_fetcher", return_value=mock_fetcher):
        activity = ContentActivities()
        result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=sources))

    assert result.total_sources == 1
    assert mock_fetcher.fetch_content.call_count == 1


@pytest.mark.asyncio
async def test_fetch_sources_parallel_all_inactive():
    """Test fetch with all inactive sources."""
    sources = [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Feed 1",
            is_active=False,
        ),
        sc.ContentSourceConfig(
            id="source_002",
            source_type="rss",
            source_url="https://example.com/feed2.xml",
            source_name="Feed 2",
            is_active=False,
        ),
    ]

    activity = ContentActivities()
    result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=sources))

    assert result.total_sources == 0
    assert result.successful_sources == 0
    assert result.failed_sources == 0
    assert result.total_articles == 0


@pytest.mark.asyncio
async def test_fetch_sources_parallel_total_failure():
    """Test when all sources fail."""
    mock_fetcher = AsyncMock()
    mock_fetcher.fetch_content = AsyncMock(side_effect=InvalidUrlError("Invalid feed URL"))

    sources = [
        sc.ContentSourceConfig(
            id="source_001",
            source_type="rss",
            source_url="https://example.com/feed1.xml",
            source_name="Feed 1",
            is_active=True,
        ),
        sc.ContentSourceConfig(
            id="source_002",
            source_type="rss",
            source_url="https://example.com/feed2.xml",
            source_name="Feed 2",
            is_active=True,
        ),
    ]

    with patch("app.temporal.activities.content.create_fetcher", return_value=mock_fetcher):
        activity = ContentActivities()
        result = await activity.fetch_sources_parallel(sc.FetchSourcesParallelRequest(sources=sources))

    assert result.total_sources == 2
    assert result.successful_sources == 0
    assert result.failed_sources == 2
    assert result.total_articles == 0
    assert len(result.fetch_errors) == 2
