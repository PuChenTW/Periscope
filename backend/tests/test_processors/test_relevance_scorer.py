"""
Tests for RelevanceScorer implementation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, Field, HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import PersonalizationSettings
from app.processors.fetchers.base import Article
from app.processors.relevance_scorer import (
    RelevanceScorer,
    SemanticRelevanceResult,
)


class MockInterestProfile(BaseModel):
    """Mock interest profile for testing (Pydantic-only, no SQLModel)."""

    id: str
    config_id: str
    keywords: list[str] = []
    relevance_threshold: int = Field(default=40, ge=0, le=100)
    boost_factor: float = Field(default=1.0, ge=0.5, le=2.0)


class TestRelevanceScorer:
    """Test RelevanceScorer functionality."""

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
    def custom_settings(self):
        """Create custom settings for testing."""
        return PersonalizationSettings(
            keyword_weight_title=3,
            keyword_weight_content=2,
            keyword_weight_tags=4,
            max_keywords=50,
            relevance_threshold_default=40,
            boost_factor_default=1.0,
            cache_ttl_minutes=720,
            enable_semantic_scoring=True,
        )

    @pytest.fixture
    def relevance_scorer(self, mock_ai_provider, custom_settings):
        """Create RelevanceScorer instance for testing."""
        scorer = RelevanceScorer(
            settings=custom_settings,
            ai_provider=mock_ai_provider,
        )
        return scorer

    @pytest.fixture
    def sample_profile(self):
        """Create sample interest profile."""
        return MockInterestProfile(
            id="test-profile-id",
            config_id="test-config-id",
            keywords=["AI", "Machine Learning", "Python"],
            relevance_threshold=40,
            boost_factor=1.0,
        )

    @pytest.fixture
    def sample_article(self):
        """Create sample article for testing."""
        return Article(
            title="Introduction to Machine Learning with Python",
            url=HttpUrl("https://example.com/ml-python"),
            content=(
                "Machine learning is a subset of artificial intelligence that focuses on "
                "building systems that learn from data. Python is the most popular language "
                "for machine learning due to its extensive libraries and simplicity."
            ),
            published_at=datetime.now(UTC),
            fetch_timestamp=datetime.now(UTC),
            tags=["Python", "AI", "tutorial"],
            ai_topics=["machine learning", "programming"],
            metadata={"quality_score": 85},
        )

    @pytest.mark.asyncio
    async def test_empty_profile_passes_threshold(self, relevance_scorer):
        """Test that articles pass threshold when profile has no keywords."""
        empty_profile = MockInterestProfile(
            id="test-profile-id",
            config_id="test-config-id",
            keywords=[],
            relevance_threshold=40,
            boost_factor=1.0,
        )

        article = Article(
            title="Random Article",
            url=HttpUrl("https://example.com/random"),
            content="Some random content",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await relevance_scorer.score_article(article, empty_profile)

        assert result.relevance_score == 0
        assert result.passes_threshold is True

    @pytest.mark.asyncio
    async def test_keyword_scoring_high_match_in_title(self, relevance_scorer, sample_profile, sample_article):
        """Test keyword scoring with high match in title."""
        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(sample_article, sample_profile)
        breakdown = result.breakdown

        assert breakdown.keyword_score >= 6
        assert "machine learning" in breakdown.matched_keywords or "python" in breakdown.matched_keywords

    @pytest.mark.asyncio
    async def test_keyword_scoring_content_match(self, relevance_scorer, sample_profile):
        """Test keyword scoring with matches in content only."""
        article = Article(
            title="A Different Topic Entirely",
            url=HttpUrl("https://example.com/other"),
            content="This article discusses Python and AI extensively, covering machine learning concepts.",
            fetch_timestamp=datetime.now(UTC),
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(article, sample_profile)
        breakdown = result.breakdown

        assert breakdown.keyword_score > 0
        assert len(breakdown.matched_keywords) > 0

    @pytest.mark.asyncio
    async def test_keyword_scoring_tag_match(self, relevance_scorer, sample_profile):
        """Test keyword scoring with matches in tags."""
        article = Article(
            title="Unrelated Title",
            url=HttpUrl("https://example.com/tags"),
            content="Completely different content here.",
            fetch_timestamp=datetime.now(UTC),
            tags=["Machine Learning", "AI"],
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(article, sample_profile)
        breakdown = result.breakdown

        assert breakdown.keyword_score >= 8
        assert "machine learning" in breakdown.matched_keywords or "ai" in breakdown.matched_keywords

    @pytest.mark.asyncio
    async def test_semantic_scoring_integration(self, relevance_scorer, sample_profile):
        """Test AI semantic scoring integration."""
        # Create article with many keyword matches in tags to trigger AI (keyword_score > 15)
        # Tags have weight 4, so 5 tags x 4 = 20 points (enough to trigger AI at > 15)
        test_profile = MockInterestProfile(
            id="test-profile-id",
            config_id="test-config-id",
            keywords=["AI", "Python", "neural", "deep", "learning"],
            relevance_threshold=40,
            boost_factor=1.0,
        )

        article_for_ai = Article(
            title="Tutorial on Technology",  # Avoid title matches to isolate tag scoring
            url=HttpUrl("https://example.com/ml-python"),
            content="This is a comprehensive technology guide.",  # No keyword matches in content
            published_at=datetime.now(UTC),
            fetch_timestamp=datetime.now(UTC),
            tags=["AI", "Python", "neural", "deep", "learning"],  # All 5 keywords in tags = 20 points
            ai_topics=["artificial intelligence"],
            metadata={"quality_score": 85},
        )

        # Mock AI response
        test_model = TestModel(
            custom_output_args=SemanticRelevanceResult(
                semantic_score=25.0,
                matched_interests=["AI", "Python"],
                reasoning="Article directly covers user's interests",
                confidence=0.95,
            )
        )

        with relevance_scorer.agent.override(model=test_model):
            result = await relevance_scorer.score_article(article_for_ai, test_profile)

            breakdown = result.breakdown

            # Should include semantic score (keyword_score=20, triggers AI because 16 <= 20 < 55)
            assert breakdown.keyword_score == 20  # 5 tags x 4
            assert breakdown.semantic_score == 25.0
            assert breakdown.final_score > breakdown.keyword_score

    @pytest.mark.asyncio
    async def test_temporal_boost_fresh_article(self, relevance_scorer, sample_profile):
        """Test temporal boost for fresh articles (< 24 hours)."""
        # Create article published 6 hours ago
        fresh_article = Article(
            title="Breaking: AI News",
            url=HttpUrl("https://example.com/fresh"),
            content="Fresh content about artificial intelligence and machine learning",
            published_at=datetime.now(UTC) - timedelta(hours=6),
            fetch_timestamp=datetime.now(UTC),
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(fresh_article, sample_profile)

        breakdown = result.breakdown

        # Fresh article should get temporal boost (linear decay from 5 to 0 over 24h)
        assert breakdown.temporal_boost > 0
        assert breakdown.temporal_boost <= 5

    @pytest.mark.asyncio
    async def test_temporal_boost_old_article(self, relevance_scorer, sample_profile, sample_article):
        """Test no temporal boost for old articles (> 24 hours)."""
        # Modify article to be 48 hours old
        sample_article.published_at = datetime.now(UTC) - timedelta(hours=48)

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(sample_article, sample_profile)

        breakdown = result.breakdown

        # Old article should get no temporal boost
        assert breakdown.temporal_boost == 0

    @pytest.mark.asyncio
    async def test_quality_boost_high_quality_with_matches(self, relevance_scorer, sample_profile, sample_article):
        """Test quality boost for high-quality articles with keyword matches."""
        # Article already has quality_score=85 and matches keywords
        relevance_scorer.settings.enable_semantic_scoring = False

        # Pass quality_score as parameter (no longer in article.metadata)
        result = await relevance_scorer.score_article(sample_article, sample_profile, quality_score=85)

        breakdown = result.breakdown

        # High quality with matches should get boost
        assert breakdown.quality_boost == 5

    @pytest.mark.asyncio
    async def test_quality_boost_no_keyword_matches(self, relevance_scorer, sample_profile):
        """Test no quality boost without keyword matches."""
        article = Article(
            title="Unrelated High Quality Article",
            url=HttpUrl("https://example.com/quality"),
            content="This is about completely different topics like gardening and cooking.",
            fetch_timestamp=datetime.now(UTC),
            metadata={"quality_score": 90},
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(article, sample_profile)

        breakdown = result.breakdown

        # No keyword matches → no quality boost
        assert breakdown.quality_boost == 0

    @pytest.mark.asyncio
    async def test_boost_factor_amplification(self, relevance_scorer, sample_article):
        """Test user boost factor amplifies final score."""
        profile_with_boost = MockInterestProfile(
            id="test-profile-id",
            config_id="test-config-id",
            keywords=["AI", "Machine Learning"],
            relevance_threshold=40,
            boost_factor=1.5,  # 50% boost
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(sample_article, profile_with_boost)

        breakdown = result.breakdown

        # Final score should be boosted
        raw_score = breakdown.keyword_score + breakdown.temporal_boost + breakdown.quality_boost
        expected_boosted = int(raw_score * 1.5)
        assert breakdown.final_score >= expected_boosted or breakdown.final_score == 100  # clamped

    @pytest.mark.asyncio
    async def test_threshold_pass(self, relevance_scorer):
        """Test article passes threshold."""
        # Use 15 single-word keywords for maximum tag scoring potential
        test_profile = MockInterestProfile(
            id="test-profile-id",
            config_id="test-config-id",
            keywords=[
                "ai",
                "python",
                "neural",
                "deep",
                "learning",
                "data",
                "science",
                "ml",
                "algorithm",
                "model",
                "train",
                "test",
                "code",
                "tech",
                "guide",
            ],
            relevance_threshold=40,
            boost_factor=1.0,
        )

        # Create article with many tags matching keywords (tags have weight 4 each)
        # 15 keywords x 4 points = 60 points (clamped to 60) + temporal(4) + quality(5) = 69 total
        strong_match_article = Article(
            title="Tutorial on Technology",  # Avoid title matches
            url=HttpUrl("https://example.com/strong-match"),
            content="Guide to modern techniques",  # Avoid content matches
            published_at=datetime.now(UTC),
            fetch_timestamp=datetime.now(UTC),
            tags=[
                "ai",
                "python",
                "neural",
                "deep",
                "learning",
                "data",
                "science",
                "ml",
                "algorithm",
                "model",
                "train",
                "test",
                "code",
                "tech",
                "guide",
            ],
            ai_topics=["artificial intelligence"],
            metadata={"quality_score": 90},
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(strong_match_article, test_profile)

        # Article with many tag matches should easily pass threshold of 40
        assert result.passes_threshold is True
        assert result.relevance_score >= 40

    @pytest.mark.asyncio
    async def test_threshold_fail(self, relevance_scorer, sample_article):
        """Test article fails threshold with no matches."""
        profile_no_match = MockInterestProfile(
            id="test-profile-id",
            config_id="test-config-id",
            keywords=["blockchain", "cryptocurrency"],  # No matches in article
            relevance_threshold=40,
            boost_factor=1.0,
        )

        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(sample_article, profile_no_match)

        # Article with no keyword matches should fail threshold
        assert result.passes_threshold is False

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_ai_failure_graceful_degradation(self, relevance_scorer, sample_profile):
        """Test graceful fallback when AI fails."""
        article_for_ai = Article(
            title="Machine Learning and AI with Python Tutorial",
            url=HttpUrl("https://example.com/ml-python"),
            content=(
                "Artificial intelligence and machine learning guide. "
                "Python AI development with machine learning algorithms."
            ),
            published_at=datetime.now(UTC),
            fetch_timestamp=datetime.now(UTC),
            tags=["Python", "AI", "Machine Learning"],
            ai_topics=["machine learning", "artificial intelligence"],
            metadata={"quality_score": 85},
        )

        relevance_scorer.agent.run = AsyncMock(side_effect=Exception("AI service error"))

        result = await relevance_scorer.score_article(article_for_ai, sample_profile)
        breakdown = result.breakdown

        assert breakdown.keyword_score > 0
        assert breakdown.semantic_score == 0.0
        assert result.relevance_score is not None

    def test_build_keyword_index(self, relevance_scorer, sample_article):
        """Test keyword index building."""
        index = relevance_scorer._build_keyword_index(sample_article)

        assert "title" in index
        assert "content" in index
        assert "tags" in index

        # Check normalization (lowercase, tokenized)
        assert "machine" in index["title"]
        assert "learning" in index["title"]
        assert "python" in index["content"]

    def test_score_keyword_matches_multi_word_keywords(self, relevance_scorer):
        """Test scoring with multi-word keywords."""
        keywords = ["machine learning", "artificial intelligence"]
        keyword_index = {
            "title": ["introduction", "to", "machine", "learning"],
            "content": ["artificial", "intelligence", "and", "data"],
            "tags": [],
        }

        score, matched = relevance_scorer._score_keyword_matches(keywords, keyword_index)

        # "machine learning" in title (weight 3)
        # "artificial intelligence" in content (weight 2)
        assert score == 5
        assert "machine learning" in matched
        assert "artificial intelligence" in matched

    def test_score_keyword_matches_clamped_to_60(self, relevance_scorer):
        """Test keyword score clamped to maximum of 60."""
        # Create many matching keywords
        keywords = [f"keyword{i}" for i in range(50)]
        keyword_index = {
            "title": [f"keyword{i}" for i in range(50)],
            "content": [],
            "tags": [],
        }

        score, matched = relevance_scorer._score_keyword_matches(keywords, keyword_index)

        # Score should be clamped to 60
        assert score == 60
        assert set(matched) == set(keywords)

    @pytest.mark.asyncio
    async def test_metadata_structure(self, relevance_scorer, sample_profile, sample_article):
        """Test final metadata structure in article."""
        relevance_scorer.settings.enable_semantic_scoring = False

        result = await relevance_scorer.score_article(sample_article, sample_profile)

        # Check all expected metadata fields present

        # Check breakdown structure
        breakdown = result.breakdown
        assert breakdown.keyword_score is not None
        assert breakdown.semantic_score is not None
        assert breakdown.temporal_boost is not None
        assert breakdown.quality_boost is not None
        assert breakdown.final_score is not None
        assert breakdown.matched_keywords is not None
        assert breakdown.threshold_passed is not None
