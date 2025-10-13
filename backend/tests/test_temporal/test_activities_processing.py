"""
Integration tests for Temporal processing activities.

Tests the score_relevance_batch activity with various scenarios including
caching, error handling, and observability metrics.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import DigestConfiguration, InterestProfile, User
from app.processors.fetchers.base import Article
from app.processors.relevance_scorer import SemanticRelevanceResult
from app.temporal.activities.processing import (
    BatchRelevanceRequest,
    compute_relevance_cache_key,
    score_relevance_batch,
)


class TestComputeRelevanceCacheKey:
    """Test cache key computation."""

    def test_cache_key_format(self):
        """Test cache key has correct format."""
        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Test content",
            fetch_timestamp=datetime.now(UTC),
        )

        cache_key = compute_relevance_cache_key(
            article,
            profile_keywords=["python", "ai"],
            relevance_threshold=40,
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

        key1 = compute_relevance_cache_key(article, ["python", "ai"], 40, 1.0)
        key2 = compute_relevance_cache_key(article, ["python", "ai"], 40, 1.0)

        assert key1 == key2

    def test_cache_key_different_keywords(self):
        """Test different keywords produce different cache keys."""
        article = Article(
            title="Test",
            url=HttpUrl("https://example.com/test"),
            content="Test",
            fetch_timestamp=datetime.now(UTC),
        )

        key1 = compute_relevance_cache_key(article, ["python"], 40, 1.0)
        key2 = compute_relevance_cache_key(article, ["java"], 40, 1.0)

        assert key1 != key2


class TestScoreRelevanceBatch:
    """Test score_relevance_batch activity."""

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

    @pytest_asyncio.fixture
    async def sample_profile(self, session: AsyncSession):
        """Create sample interest profile in database."""

        # Create user
        user = User(
            email="test@example.com",
            hashed_password="fake_hash",
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create digest config
        config = DigestConfiguration(
            user_id=user.id,
            delivery_time=datetime.now(UTC).time(),
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)

        # Create interest profile
        profile = InterestProfile(
            config_id=config.id,
            keywords=["python", "ai", "machine learning"],
            relevance_threshold=40,
            boost_factor=1.0,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return profile

    @pytest.mark.asyncio
    async def test_score_relevance_batch_happy_path(self, sample_articles, sample_profile, redis_client):
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

            request = BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
                quality_scores={
                    str(sample_articles[0].url): 85,
                    str(sample_articles[1].url): 75,
                },
            )

            result = await score_relevance_batch(request)

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
            for url, relevance_result in result.relevance_results.items():
                assert 0 <= relevance_result.relevance_score <= 100
                assert relevance_result.breakdown is not None

    @pytest.mark.asyncio
    async def test_score_relevance_batch_idempotency(self, sample_articles, sample_profile, redis_client):
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

            request = BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
            )

            # First call - should score articles
            result1 = await score_relevance_batch(request)
            assert result1.cache_hits == 0
            assert result1.total_scored == 2

            # Second call - should hit cache
            result2 = await score_relevance_batch(request)
            assert result2.cache_hits == 2
            assert result2.total_scored == 2

            # Results should be identical
            assert result1.relevance_results.keys() == result2.relevance_results.keys()

    @pytest.mark.asyncio
    async def test_score_relevance_batch_empty_profile(self, sample_articles, sample_profile, redis_client):
        """Test handling of empty profile (no keywords)."""
        # Update profile to have no keywords
        sample_profile.keywords = []

        # Mock AI provider
        with patch("app.temporal.activities.processing.create_ai_provider") as mock_ai_factory:
            mock_provider = MagicMock()
            mock_provider.create_agent = MagicMock()
            mock_ai_factory.return_value = mock_provider

            request = BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
            )

            result = await score_relevance_batch(request)

            # All articles should get score=0 but pass threshold
            assert result.total_scored == 2
            for relevance_result in result.relevance_results.values():
                assert relevance_result.relevance_score == 0
                assert relevance_result.passes_threshold is True

    @pytest.mark.asyncio
    async def test_score_relevance_batch_ai_failure(self, sample_articles, sample_profile, redis_client):
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

            request = BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=sample_articles,
            )

            result = await score_relevance_batch(request)

            # Should still score articles with deterministic scoring (no AI)
            assert result.total_scored == 2
            assert result.errors_count == 0  # AI failure is handled gracefully, not counted as error

            # Verify semantic scores are 0 (AI failed/skipped)
            for relevance_result in result.relevance_results.values():
                assert relevance_result.breakdown.semantic_score == 0.0

    @pytest.mark.asyncio
    async def test_score_relevance_batch_partial_failure(self, sample_articles, sample_profile, redis_client):
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

            # Patch scorer to fail on bad article
            original_score = None

            async def mock_score_article(article, profile, quality_score=None):
                if str(article.url) == str(bad_article.url):
                    raise Exception("Scoring failed for this article")
                return await original_score(article, profile, quality_score)

            with patch("app.processors.relevance_scorer.RelevanceScorer.score_article", side_effect=mock_score_article):
                request = BatchRelevanceRequest(
                    profile_id=sample_profile.id,
                    articles=articles,
                )

                result = await score_relevance_batch(request)

                # Should have partial results (2 good articles)
                assert result.total_scored == 2
                assert result.errors_count == 1
                assert str(bad_article.url) not in result.relevance_results

    @pytest.mark.asyncio
    async def test_score_relevance_batch_cache_behavior(self, sample_articles, sample_profile, redis_client):
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

            request = BatchRelevanceRequest(
                profile_id=sample_profile.id,
                articles=[sample_articles[0]],
            )

            # First call - cache miss
            result1 = await score_relevance_batch(request)
            assert result1.cache_hits == 0
            assert result1.total_scored == 1

            # Verify result was cached
            cache_key = compute_relevance_cache_key(
                sample_articles[0],
                sample_profile.keywords,
                sample_profile.relevance_threshold,
                sample_profile.boost_factor,
            )
            cached_value = await redis_client.get(cache_key)
            assert cached_value is not None

            # Second call - cache hit
            result2 = await score_relevance_batch(request)
            assert result2.cache_hits == 1
            assert result2.total_scored == 1

            # Scores should match
            url = str(sample_articles[0].url)
            assert result1.relevance_results[url].relevance_score == result2.relevance_results[url].relevance_score
