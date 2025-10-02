"""
Tests for SimilarityDetector implementation using PydanticAI
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import HttpUrl, ValidationError
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.processors.fetchers.base import Article
from app.processors.similarity_detector import ArticleGroup, SimilarityDetector, SimilarityScore


class TestSimilarityDetector:
    """Test SimilarityDetector functionality."""

    @pytest.fixture
    def mock_ai_provider(self):
        """Create a mock AI provider for testing."""
        mock_provider = MagicMock()

        def create_agent_mock(output_type, system_prompt):
            # Create agent with TestModel for deterministic testing
            return Agent(TestModel(), output_type=output_type, system_prompt=system_prompt)

        mock_provider.create_agent = create_agent_mock
        return mock_provider

    @pytest.fixture
    def similarity_detector(self, mock_ai_provider):
        """Create SimilarityDetector instance for testing."""
        with patch("app.processors.similarity_detector.get_redis_client") as mock_redis:
            mock_redis.return_value = AsyncMock()
            detector = SimilarityDetector(ai_provider=mock_ai_provider)
            detector.redis_client = mock_redis.return_value
            return detector

    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing."""
        return [
            Article(
                title="OpenAI Launches GPT-5 with Revolutionary Features",
                url=HttpUrl("https://example.com/article1"),
                content=(
                    "OpenAI has announced the release of GPT-5, their latest language model with "
                    "groundbreaking capabilities..."
                ),
                published_at=datetime(2024, 1, 15, 10, 0),
                tags=["AI", "OpenAI", "GPT"],
            ),
            Article(
                title="GPT-5 Release: What You Need to Know",
                url=HttpUrl("https://another-site.com/article2"),
                content=(
                    "The new GPT-5 model from OpenAI brings significant improvements over GPT-4, "
                    "including better reasoning..."
                ),
                published_at=datetime(2024, 1, 15, 11, 0),
                tags=["technology", "artificial intelligence"],
            ),
            Article(
                title="Scientists Discover New Planet in Distant Solar System",
                url=HttpUrl("https://example.com/article3"),
                content=(
                    "Astronomers have identified a new exoplanet orbiting a star 500 light-years away from Earth..."
                ),
                published_at=datetime(2024, 1, 15, 9, 0),
                tags=["space", "astronomy"],
            ),
        ]

    @pytest.mark.asyncio
    async def test_detect_similar_articles_empty_list(self, similarity_detector):
        """Test with empty article list."""
        result = await similarity_detector.detect_similar_articles([])
        assert result == []

    @pytest.mark.asyncio
    async def test_detect_similar_articles_single_article(self, similarity_detector, sample_articles):
        """Test with single article returns single group."""
        result = await similarity_detector.detect_similar_articles([sample_articles[0]])

        assert len(result) == 1
        assert result[0].primary_article == sample_articles[0]
        assert len(result[0].similar_articles) == 0

    @pytest.mark.asyncio
    async def test_compare_articles_with_test_model(self, similarity_detector, sample_articles):
        """Test article comparison using TestModel."""
        # Override agent with TestModel for deterministic testing
        test_model = TestModel(
            custom_output_args=SimilarityScore(
                confidence=0.95,
                reasoning="Both articles discuss GPT-5 release",
            )
        )

        with similarity_detector.agent.override(model=test_model):
            # Mock cache to return None (no cached result)
            similarity_detector.redis_client.get.return_value = None

            is_similar = await similarity_detector._compare_articles(sample_articles[0], sample_articles[1])

            assert is_similar is True

    @pytest.mark.asyncio
    async def test_compare_articles_not_similar(self, similarity_detector, sample_articles):
        """Test article comparison for dissimilar articles."""
        # Override agent with TestModel
        test_model = TestModel(
            custom_output_args=SimilarityScore(
                confidence=0.1,
                reasoning="Articles cover completely different topics",
            )
        )

        with similarity_detector.agent.override(model=test_model):
            similarity_detector.redis_client.get.return_value = None

            is_similar = await similarity_detector._compare_articles(sample_articles[0], sample_articles[2])

            assert is_similar is False

    @pytest.mark.asyncio
    async def test_compare_articles_below_threshold(self, similarity_detector, sample_articles):
        """Test article comparison with confidence below threshold."""
        # Override agent with TestModel
        test_model = TestModel(
            custom_output_args=SimilarityScore(
                confidence=0.5,  # Below default threshold of 0.7
                reasoning="Somewhat related but not closely",
            )
        )

        with similarity_detector.agent.override(model=test_model):
            similarity_detector.redis_client.get.return_value = None

            is_similar = await similarity_detector._compare_articles(sample_articles[0], sample_articles[1])

            # Should be False because confidence is below threshold
            assert is_similar is False

    @pytest.mark.asyncio
    async def test_detect_similar_articles_groups_similar_ones(self, similarity_detector, sample_articles):
        """Test that similar articles are grouped together and topics are merged from ai_topics."""
        # Add ai_topics to articles
        sample_articles[0].ai_topics = ["GPT-5", "OpenAI", "AI"]
        sample_articles[1].ai_topics = ["GPT-5", "Language Models"]
        sample_articles[2].ai_topics = ["Space", "Astronomy"]

        # Setup: Articles 0 and 1 are similar, Article 2 is different
        async def mock_compare(article1, article2):
            return (article1 == sample_articles[0] and article2 == sample_articles[1]) or (
                article1 == sample_articles[1] and article2 == sample_articles[0]
            )

        with patch.object(similarity_detector, "_compare_articles", side_effect=mock_compare):
            groups = await similarity_detector.detect_similar_articles(sample_articles)

            # Should have 2 groups: one with articles 0 and 1, one with article 2
            assert len(groups) == 2

            # Find the group with multiple articles
            multi_article_group = next((g for g in groups if len(g.similar_articles) > 0), None)
            single_article_group = next((g for g in groups if len(g.similar_articles) == 0), None)

            assert multi_article_group is not None
            assert single_article_group is not None

            # The multi-article group should have 2 articles total
            total_articles = 1 + len(multi_article_group.similar_articles)  # primary + similar
            assert total_articles == 2

            # Verify topics are merged from ai_topics of both articles
            assert "GPT-5" in multi_article_group.common_topics
            assert "OpenAI" in multi_article_group.common_topics
            assert "AI" in multi_article_group.common_topics
            assert "Language Models" in multi_article_group.common_topics

            # Single article group should have topics from its ai_topics
            assert "Space" in single_article_group.common_topics
            assert "Astronomy" in single_article_group.common_topics

    @pytest.mark.asyncio
    async def test_detect_similar_articles_all_similar(self, similarity_detector, sample_articles):
        """Test when all articles are similar."""

        async def mock_compare_all_similar(_article1, _article2):
            return True

        with patch.object(similarity_detector, "_compare_articles", side_effect=mock_compare_all_similar):
            groups = await similarity_detector.detect_similar_articles(sample_articles)

            # All articles should be in one group
            assert len(groups) == 1
            total_articles = 1 + len(groups[0].similar_articles)
            assert total_articles == len(sample_articles)

    @pytest.mark.asyncio
    async def test_detect_similar_articles_none_similar(self, similarity_detector, sample_articles):
        """Test when no articles are similar."""

        async def mock_compare_none_similar(_article1, _article2):
            return False

        with patch.object(similarity_detector, "_compare_articles", side_effect=mock_compare_none_similar):
            groups = await similarity_detector.detect_similar_articles(sample_articles)

            # Each article should be in its own group
            assert len(groups) == len(sample_articles)
            for group in groups:
                assert len(group.similar_articles) == 0

    @pytest.mark.asyncio
    async def test_cache_hit(self, similarity_detector, sample_articles):
        """Test that cached results are used when available."""

        # Mock cached result
        cached_data = json.dumps({"is_similar": True})
        similarity_detector.redis_client.get.return_value = cached_data

        is_similar = await similarity_detector._compare_articles(sample_articles[0], sample_articles[1])

        # Should use cached result
        assert is_similar is True

        # Agent should not be called (no AI request made)
        similarity_detector.redis_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_stores_result(self, similarity_detector, sample_articles):
        """Test that comparison results are cached."""
        # Mock cache miss
        similarity_detector.redis_client.get.return_value = None

        # Override agent with TestModel
        test_model = TestModel(custom_output_args=SimilarityScore(confidence=0.9, reasoning="Similar articles"))

        with similarity_detector.agent.override(model=test_model):
            await similarity_detector._compare_articles(sample_articles[0], sample_articles[1])

            # Verify cache was written to
            similarity_detector.redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_comparison(self, similarity_detector, sample_articles):
        """Test that errors during comparison are handled gracefully."""
        similarity_detector.redis_client.get.return_value = None

        # Make agent raise an exception
        with patch.object(similarity_detector.agent, "run", side_effect=Exception("AI service error")):
            is_similar = await similarity_detector._compare_articles(sample_articles[0], sample_articles[1])

            # Should return False on error to avoid false grouping
            assert is_similar is False

    def test_generate_group_id_consistency(self, similarity_detector, sample_articles):
        """Test that group ID generation is consistent for same articles."""
        group_id_1 = similarity_detector._generate_group_id([sample_articles[0], sample_articles[1]])
        group_id_2 = similarity_detector._generate_group_id([sample_articles[0], sample_articles[1]])

        assert group_id_1 == group_id_2

    def test_generate_group_id_order_independent(self, similarity_detector, sample_articles):
        """Test that group ID is same regardless of article order."""
        group_id_1 = similarity_detector._generate_group_id([sample_articles[0], sample_articles[1]])
        group_id_2 = similarity_detector._generate_group_id([sample_articles[1], sample_articles[0]])

        assert group_id_1 == group_id_2

    def test_generate_cache_key_order_independent(self, similarity_detector, sample_articles):
        """Test that cache key is same regardless of article order."""
        key_1 = similarity_detector._generate_cache_key(sample_articles[0], sample_articles[1])
        key_2 = similarity_detector._generate_cache_key(sample_articles[1], sample_articles[0])

        assert key_1 == key_2

    def test_build_comparison_prompt(self, similarity_detector, sample_articles):
        """Test that comparison prompt is built correctly."""
        prompt = similarity_detector._build_comparison_prompt(sample_articles[0], sample_articles[1])

        assert sample_articles[0].title in prompt
        assert sample_articles[1].title in prompt
        assert "Are these articles covering the same story, topic, or event?" in prompt

    @pytest.mark.asyncio
    async def test_similarity_score_model_validation(self):
        """Test SimilarityScore Pydantic model validation."""
        # Valid score
        score = SimilarityScore(confidence=0.85, reasoning="Test")

        assert score.confidence == 0.85

        # Test confidence bounds
        with pytest.raises(ValidationError):  # Should fail validation
            SimilarityScore(confidence=1.5, reasoning="Test")

    def test_article_group_model(self, sample_articles):
        """Test ArticleGroup Pydantic model."""
        group = ArticleGroup(
            primary_article=sample_articles[0],
            similar_articles=[sample_articles[1]],
            common_topics=["AI", "GPT"],
            group_id="test-group-id",
        )

        assert group.primary_article == sample_articles[0]
        assert len(group.similar_articles) == 1
        assert "AI" in group.common_topics
        assert group.group_id == "test-group-id"
        assert isinstance(group.created_at, datetime)

    @pytest.mark.asyncio
    async def test_detect_similar_articles_preserves_topics(self, similarity_detector, sample_articles):
        """Test that topics from article ai_topics are preserved in final groups."""
        # Add ai_topics to articles
        sample_articles[0].ai_topics = ["GPT-5", "OpenAI", "AI"]
        sample_articles[1].ai_topics = ["GPT-5", "Machine Learning"]

        async def mock_compare(article1, article2):
            return (article1 == sample_articles[0] and article2 == sample_articles[1]) or (
                article1 == sample_articles[1] and article2 == sample_articles[0]
            )

        with patch.object(similarity_detector, "_compare_articles", side_effect=mock_compare):
            groups = await similarity_detector.detect_similar_articles(sample_articles)

            # Find the group with multiple articles
            multi_article_group = next((g for g in groups if len(g.similar_articles) > 0), None)

            assert multi_article_group is not None
            assert "GPT-5" in multi_article_group.common_topics
            assert "OpenAI" in multi_article_group.common_topics
            assert "AI" in multi_article_group.common_topics
            assert "Machine Learning" in multi_article_group.common_topics

    @pytest.mark.asyncio
    async def test_detect_similar_articles_aggregates_topics_from_multiple_articles(
        self, similarity_detector, sample_articles
    ):
        """Test that topics from multiple articles are aggregated when 3+ articles form a group."""
        # Create 4th article for testing
        article4 = Article(
            title="OpenAI GPT-5: Technical Deep Dive",
            url=HttpUrl("https://techblog.com/gpt5-technical"),
            content="A technical analysis of the new GPT-5 architecture and its improvements...",
            published_at=datetime(2024, 1, 15, 12, 0),
            tags=["AI", "technology"],
            ai_topics=["GPT-5", "Neural Networks", "Technology"],
        )
        test_articles = [*sample_articles[:2], article4]
        # Add ai_topics to existing articles
        test_articles[0].ai_topics = ["GPT-5", "OpenAI"]
        test_articles[1].ai_topics = ["GPT-5", "AI", "Machine Learning"]

        async def mock_compare(article1, article2):
            # All three articles are similar
            return article1 in test_articles and article2 in test_articles

        with patch.object(similarity_detector, "_compare_articles", side_effect=mock_compare):
            groups = await similarity_detector.detect_similar_articles(test_articles)

            # All three articles should be in one group
            assert len(groups) == 1
            group = groups[0]

            # Should aggregate topics from all three articles
            assert "GPT-5" in group.common_topics
            assert "OpenAI" in group.common_topics
            assert "AI" in group.common_topics
            assert "Machine Learning" in group.common_topics
            assert "Neural Networks" in group.common_topics
            assert "Technology" in group.common_topics

    @pytest.mark.asyncio
    async def test_detect_similar_articles_deduplicates_topics(self, similarity_detector, sample_articles):
        """Test that duplicate topics across articles are deduplicated."""
        # Add ai_topics with duplicates across articles
        sample_articles[0].ai_topics = ["AI", "GPT", "OpenAI"]
        sample_articles[1].ai_topics = ["AI", "GPT", "Machine Learning"]

        async def mock_compare(article1, article2):
            return (article1 == sample_articles[0] and article2 == sample_articles[1]) or (
                article1 == sample_articles[1] and article2 == sample_articles[0]
            )

        with patch.object(similarity_detector, "_compare_articles", side_effect=mock_compare):
            groups = await similarity_detector.detect_similar_articles(sample_articles)

            # Find the group with multiple articles
            multi_article_group = next((g for g in groups if len(g.similar_articles) > 0), None)

            assert multi_article_group is not None
            # Topics should be deduplicated
            assert multi_article_group.common_topics.count("AI") == 1
            assert multi_article_group.common_topics.count("GPT") == 1
            assert multi_article_group.common_topics.count("OpenAI") == 1
            assert multi_article_group.common_topics.count("Machine Learning") == 1

    @pytest.mark.asyncio
    async def test_single_article_empty_topics(self, similarity_detector, sample_articles):
        """Test that single-article groups have empty topics when article has no ai_topics."""
        # Ensure article has no ai_topics
        sample_articles[0].ai_topics = None

        result = await similarity_detector.detect_similar_articles([sample_articles[0]])

        assert len(result) == 1
        assert result[0].common_topics == []

    @pytest.mark.asyncio
    async def test_single_article_with_topics(self, similarity_detector, sample_articles):
        """Test that single-article groups preserve ai_topics from the article."""
        # Set ai_topics on the article
        sample_articles[0].ai_topics = ["AI", "Technology"]

        result = await similarity_detector.detect_similar_articles([sample_articles[0]])

        assert len(result) == 1
        assert result[0].common_topics == ["AI", "Technology"]
