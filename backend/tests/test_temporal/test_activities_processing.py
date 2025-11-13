"""
Integration tests for Temporal processing activities.

Tests the score_relevance_batch activity with various scenarios including
caching, error handling, and observability metrics.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from sqlmodel import Session

from app.models.users import DigestConfiguration, InterestProfile, User
from app.processors.fetchers.base import Article
from app.processors.relevance_scorer import RelevanceBreakdown, RelevanceResult, SemanticRelevanceResult
from app.processors.validator import SpamDetectionResult
from app.temporal.activities import schemas as sc
from app.temporal.activities.processing import ProcessingActivities
from app.utils.cache import compute_relevance_cache_key


class TestComputeRelevanceCacheKey:
    """Test cache key computation."""

    @pytest.fixture
    def activities(self):
        """Create ProcessingActivities instance for testing."""
        return ProcessingActivities()

    def test_cache_key_format(self):
        """Test cache key has correct format."""
        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Test content",
            fetch_timestamp=datetime.now(UTC),
        )

        cache_key = compute_relevance_cache_key(
            url=article.url,
            keywords=["python", "ai"],
            threshold=40,
            boost_factor=1.0,
        )

        assert cache_key.startswith("relevance:")
        assert str(article.url) in cache_key

    def test_cache_key_same_profile_content(self):
        """Test identical profile content produces same cache key."""
        article = Article(
            title="Test",
            url=HttpUrl("https://example.com/test"),
            content="Test",
            fetch_timestamp=datetime.now(UTC),
        )

        key1 = compute_relevance_cache_key(article.url, ["python", "ai"], 40, 1.0)
        key2 = compute_relevance_cache_key(article.url, ["python", "ai"], 40, 1.0)

        assert key1 == key2

    def test_cache_key_different_keywords(self):
        """Test different keywords produce different cache keys."""
        article = Article(
            title="Test",
            url=HttpUrl("https://example.com/test"),
            content="Test",
            fetch_timestamp=datetime.now(UTC),
        )

        key1 = compute_relevance_cache_key(article.url, ["python"], 40, 1.0)
        key2 = compute_relevance_cache_key(article.url, ["java"], 40, 1.0)

        assert key1 != key2


class TestScoreRelevanceBatch:
    """Test score_relevance_batch activity."""

    @pytest.fixture
    def activities(self):
        """Create ProcessingActivities instance for testing."""
        return ProcessingActivities()

    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing."""
        return [
            Article(
                title="Python AI Tutorial",
                url=HttpUrl("https://example.com/article1"),
                content="Learn Python for artificial intelligence and machine learning applications.",
                fetch_timestamp=datetime.now(UTC),
                published_at=datetime.now(UTC),
                tags=["python", "ai"],
            ),
            Article(
                title="Machine Learning Basics",
                url=HttpUrl("https://example.com/article2"),
                content="Introduction to machine learning concepts and algorithms.",
                fetch_timestamp=datetime.now(UTC),
                published_at=datetime.now(UTC),
                tags=["ml", "tutorial"],
            ),
        ]

    @pytest.fixture
    def sample_user(self, session: Session):
        # Create user
        user = User(
            email="test@example.com",
            hashed_password="fake_hash",
            is_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def sample_digest_configuration(self, sample_user, session: Session):
        # Create digest config
        config = DigestConfiguration(
            user_id=sample_user.id,
            delivery_time=datetime.now(UTC).time(),
        )
        session.add(config)
        session.commit()
        session.refresh(config)
        return config

    @pytest.fixture
    def sample_profile(self, sample_digest_configuration, session: Session):
        profile = InterestProfile(
            config_id=sample_digest_configuration.id,
            keywords=["python", "ai", "machine learning"],
            relevance_threshold=40,
            boost_factor=1.0,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

        return profile

    @pytest.fixture
    def sample_empty_profile(self, sample_digest_configuration, session: Session):
        profile = InterestProfile(
            config_id=sample_digest_configuration.id,
            keywords=[],
            relevance_threshold=40,
            boost_factor=1.0,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

        return profile

    @pytest.fixture(autouse=True)
    def setup_activity_environment(self, redis_client, clear_async_db_cache):
        """Setup environment for Temporal activity tests."""
        with patch("app.temporal.activities.processing.get_redis_client", return_value=redis_client):
            yield

    @pytest.mark.asyncio
    async def test_score_relevance_batch_happy_path(self, activities, sample_articles, sample_profile):
        """Test successful batch scoring with all articles."""
        # Mock AI provider
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SemanticRelevanceResult(
                        semantic_score=20.0,
                        matched_interests=["python", "ai"],
                        reasoning="Relevant content",
                        confidence=0.9,
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider
            activities.ai_provider = mock_provider

            request = sc.BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
                quality_scores={
                    str(sample_articles[0].url): 85,
                    str(sample_articles[1].url): 75,
                },
            )

            result = await activities.score_relevance_batch(request)

            # Verify result structure
            assert result.profile_id == sample_profile.id
            assert len(result.articles) == 2
            assert result.total_scored == 2
            assert result.cache_hits == 0
            assert result.errors_count == 0
            assert result.start_timestamp < result.end_timestamp

            # Verify relevance results exist
            assert str(sample_articles[0].url) in result.relevance_results
            assert str(sample_articles[1].url) in result.relevance_results

            # Verify scores are reasonable
            for relevance_result in result.relevance_results.values():
                assert 0 <= relevance_result.relevance_score <= 100
                assert relevance_result.breakdown is not None

    @pytest.mark.asyncio
    async def test_score_relevance_batch_idempotency(self, activities, sample_articles, sample_profile):
        """Test that second call returns cached results."""
        # Mock AI provider
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SemanticRelevanceResult(
                        semantic_score=20.0,
                        matched_interests=["python"],
                        reasoning="Test",
                        confidence=0.9,
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider

            request = sc.BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
            )

            # First call - should score articles
            result1 = await activities.score_relevance_batch(request)
            assert result1.cache_hits == 0
            assert result1.total_scored == 2

            # Second call - should hit cache
            result2 = await activities.score_relevance_batch(request)
            assert result2.cache_hits == 2
            assert result2.total_scored == 2

            # Results should be identical
            assert result1.relevance_results.keys() == result2.relevance_results.keys()

    @pytest.mark.asyncio
    async def test_score_relevance_batch_empty_profile(self, activities, sample_articles, sample_empty_profile):
        """Test handling of empty profile (no keywords)."""
        # Mock AI provider
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()
            mock_provider.create_agent = MagicMock()
            mock_ai_factory.return_value = mock_provider

            request = sc.BatchRelevanceRequest(
                profile_id=sample_empty_profile.id,
                articles=sample_articles,
            )

            result = await activities.score_relevance_batch(request)

            # All articles should get score=0 but pass threshold
            assert result.total_scored == 2
            for relevance_result in result.relevance_results.values():
                assert relevance_result.relevance_score == 0
                assert relevance_result.passes_threshold is True

    @pytest.mark.asyncio
    async def test_score_relevance_batch_ai_failure(self, activities, sample_articles, sample_profile):
        """Test graceful degradation when AI fails."""
        # Mock AI provider to raise exception
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                agent = MagicMock()
                agent.run = AsyncMock(side_effect=Exception("AI service error"))
                agent.override = MagicMock()
                return agent

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider

            request = sc.BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
            )

            result = await activities.score_relevance_batch(request)

            # Should still score articles with deterministic scoring (no AI)
            assert result.total_scored == 2
            assert result.errors_count == 0  # AI failure is handled gracefully, not counted as error

            # Verify semantic scores are 0 (AI failed/skipped)
            for relevance_result in result.relevance_results.values():
                assert relevance_result.breakdown.semantic_score == 0.0

    @pytest.mark.asyncio
    async def test_score_relevance_batch_partial_failure(self, activities, sample_articles, sample_profile):
        """Test handling when some articles fail to score."""
        # Create a bad article that will cause scoring to fail
        bad_article = Article(
            title="Bad Article",
            url=HttpUrl("https://example.com/bad"),
            content="",  # Empty content might cause issues
            fetch_timestamp=datetime.now(UTC),
        )
        articles = [sample_articles[0], bad_article, sample_articles[1]]

        # Mock scorer to fail on bad article
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SemanticRelevanceResult(
                        semantic_score=20.0,
                        matched_interests=["python"],
                        reasoning="Test",
                        confidence=0.9,
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider

            async def mock_score_article(article, profile, quality_score=None):
                if str(article.url) == str(bad_article.url):
                    raise Exception("Scoring failed for this article")

                breakdown = RelevanceBreakdown(
                    keyword_score=0,
                    semantic_score=0.0,
                    temporal_boost=0,
                    quality_boost=0,
                    final_score=0,
                    matched_keywords=[],
                    threshold_passed=True,
                )
                return RelevanceResult(
                    relevance_score=0,
                    breakdown=breakdown,
                    passes_threshold=True,
                    matched_keywords=[],
                )

            with patch("app.processors.relevance_scorer.RelevanceScorer.score_article", side_effect=mock_score_article):
                request = sc.BatchRelevanceRequest(
                    profile_id=sample_profile.id,
                    articles=articles,
                )

                result = await activities.score_relevance_batch(request)

                # Should have partial results (2 good articles)
                assert result.total_scored == 2
                assert result.errors_count == 1
                assert str(bad_article.url) not in result.relevance_results

    @pytest.mark.asyncio
    async def test_score_relevance_batch_cache_behavior(
        self, activities, sample_articles, sample_profile, redis_client
    ):
        """Test cache miss then cache hit behavior."""
        # Mock AI provider
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SemanticRelevanceResult(
                        semantic_score=15.0,
                        matched_interests=["python"],
                        reasoning="Test",
                        confidence=0.85,
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider

            request = sc.BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=[sample_articles[0]],
            )

            # First call - cache miss
            result1 = await activities.score_relevance_batch(request)
            assert result1.cache_hits == 0
            assert result1.total_scored == 1

            # Verify result was cached
            cache_key = compute_relevance_cache_key(
                sample_articles[0].url,
                sample_profile.keywords,
                sample_profile.relevance_threshold,
                sample_profile.boost_factor,
            )
            cached_value = await redis_client.get(cache_key)
            assert cached_value is not None

            # Second call - cache hit
            result2 = await activities.score_relevance_batch(request)
            assert result2.cache_hits == 1
            assert result2.total_scored == 1

            # Scores should match
            url = str(sample_articles[0].url)
            assert result1.relevance_results[url].relevance_score == result2.relevance_results[url].relevance_score


class TestNormalizeArticlesBatch:
    """Test normalize_articles_batch activity."""

    @pytest.fixture
    def activities(self):
        """Create ProcessingActivities instance for testing."""
        return ProcessingActivities()

    @pytest.fixture
    def sample_raw_articles(self):
        """Create sample raw articles for testing."""
        return [
            Article(
                title="  Valid Article Title  ",
                url=HttpUrl("https://example.com/article1"),
                content="This is a valid article with sufficient content length. " * 10,
                fetch_timestamp=datetime.now(UTC),
                author="  Author Name  ",
                tags=["python", "  AI  ", ""],
            ),
            Article(
                title="Another Good Article",
                url=HttpUrl("https://example.com/article2"),
                content="Another valid article with good content. " * 10,
                fetch_timestamp=datetime.now(UTC),
                published_at=datetime.now(UTC),
            ),
        ]

    @pytest.fixture
    def spam_article(self):
        """Create a spam article for testing."""
        return Article(
            title="Buy cheap products now!!!",
            url=HttpUrl("https://spam.example.com/ads"),
            content="Click here for amazing deals! Limited time offer! Buy now! " * 5,
            fetch_timestamp=datetime.now(UTC),
        )

    @pytest.fixture
    def invalid_articles(self):
        """Create articles that should be rejected during normalization."""
        return [
            # Too short content
            Article(
                title="Short",
                url=HttpUrl("https://example.com/short"),
                content="Too short",
                fetch_timestamp=datetime.now(UTC),
            ),
            # Missing critical fields
            Article(
                title="",
                url=HttpUrl("https://example.com/notitle"),
                content="Content without title. " * 10,
                fetch_timestamp=datetime.now(UTC),
            ),
        ]

    @pytest.fixture(autouse=True)
    def setup_activity_environment(self, redis_client, clear_async_db_cache):
        """Setup environment for Temporal activity tests."""
        with patch("app.temporal.activities.processing.get_redis_client", return_value=redis_client):
            yield

    @pytest.mark.asyncio
    async def test_normalize_articles_batch_happy_path(self, activities, sample_raw_articles):
        """Test successful batch normalization with all valid articles."""
        # Mock AI provider for spam detection
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SpamDetectionResult(
                        is_spam=False,
                        confidence=0.95,
                        reasoning="Legitimate content",
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider
            activities.ai_provider = mock_provider

            request = sc.BatchNormalizationRequest(articles=sample_raw_articles)
            result = await activities.normalize_articles_batch(request)

            # Verify result structure
            assert len(result.articles) == 2
            assert result.total_processed == 2
            assert result.rejected_count == 0
            assert result.spam_detected_count == 0
            assert result.start_timestamp <= result.end_timestamp

            # Verify normalization applied (whitespace trimmed)
            assert result.articles[0].title == "Valid Article Title"
            assert result.articles[0].author == "Author Name"
            # Tags should be normalized (trimmed, empties removed)
            assert "" not in result.articles[0].tags
            assert "AI" in result.articles[0].tags or "  AI  " not in result.articles[0].tags

    @pytest.mark.asyncio
    async def test_normalize_articles_batch_idempotency(self, activities, sample_raw_articles):
        """Test that activity produces consistent results on repeated calls."""
        # Mock AI provider
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SpamDetectionResult(
                        is_spam=False,
                        confidence=0.95,
                        reasoning="Not spam",
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider
            activities.ai_provider = mock_provider

            request = sc.BatchNormalizationRequest(articles=sample_raw_articles)

            # First call
            result1 = await activities.normalize_articles_batch(request)
            assert len(result1.articles) == 2

            # Second call - should produce same results (idempotent)
            result2 = await activities.normalize_articles_batch(request)
            assert len(result2.articles) == 2

            # Verify article URLs match
            urls1 = {str(a.url) for a in result1.articles}
            urls2 = {str(a.url) for a in result2.articles}
            assert urls1 == urls2

    @pytest.mark.asyncio
    async def test_normalize_articles_batch_spam_detection(self, activities, sample_raw_articles):
        """Test spam detection integration (verifies spam detection runs without errors)."""
        # Mock AI provider for spam detection
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SpamDetectionResult(
                        is_spam=False,
                        confidence=0.95,
                        reasoning="Legitimate content",
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider
            activities.ai_provider = mock_provider

            request = sc.BatchNormalizationRequest(articles=sample_raw_articles)
            result = await activities.normalize_articles_batch(request)

            # Verify spam detection ran successfully (no crashes)
            assert result.total_processed == 2
            assert len(result.articles) == 2
            assert result.spam_detected_count == 0  # No spam detected (all passed)

    @pytest.mark.asyncio
    async def test_normalize_articles_batch_ai_failure_graceful(self, activities, sample_raw_articles):
        """Test graceful handling when AI spam detection fails."""
        # Mock AI provider to raise exception
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                agent = MagicMock()
                agent.run = AsyncMock(side_effect=Exception("AI service down"))
                agent.override = MagicMock()
                return agent

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider
            activities.ai_provider = mock_provider

            request = sc.BatchNormalizationRequest(articles=sample_raw_articles)
            result = await activities.normalize_articles_batch(request)

            # Should still normalize articles (assume not spam on AI failure)
            assert len(result.articles) == 2
            assert result.total_processed == 2
            # AI failures don't count as spam or errors (graceful fallback)
            assert result.spam_detected_count == 0

    @pytest.mark.asyncio
    async def test_normalize_articles_batch_no_filtering(self, activities, sample_raw_articles, invalid_articles):
        """Test that normalization passes through all articles without filtering.

        Note: Filtering (based on length/spam) is now done by validate_and_filter_batch.
        normalize_articles_batch only normalizes: URLs, dates, metadata.
        """
        articles = sample_raw_articles + invalid_articles

        # Mock AI provider (though it's not used in normalization anymore)
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()

            def create_agent_mock(output_type, system_prompt):
                test_model = TestModel(
                    custom_output_args=SpamDetectionResult(
                        is_spam=False,
                        confidence=0.9,
                        reasoning="Not spam",
                    )
                )
                return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

            mock_provider.create_agent = create_agent_mock
            mock_ai_factory.return_value = mock_provider
            activities.ai_provider = mock_provider

            request = sc.BatchNormalizationRequest(articles=articles)
            result = await activities.normalize_articles_batch(request)

            # All articles pass through (no filtering in normalize anymore)
            assert result.total_processed == 4
            assert len(result.articles) == 4  # All articles normalized, even short/invalid ones
            assert result.rejected_count == 0  # No rejection happens here
            assert result.spam_detected_count == 0  # No spam detection in normalization

    @pytest.mark.asyncio
    async def test_normalize_articles_batch_empty_input(self, activities):
        """Test handling of empty article list."""
        request = sc.BatchNormalizationRequest(articles=[])
        result = await activities.normalize_articles_batch(request)

        assert result.total_processed == 0
        assert len(result.articles) == 0
        assert result.rejected_count == 0
        assert result.spam_detected_count == 0
