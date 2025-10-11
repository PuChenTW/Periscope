"""
Tests for QualityScorer implementation
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import ContentNormalizationSettings
from app.processors.fetchers.base import Article
from app.processors.quality_scorer import AIContentQualityResult, QualityScorer


class TestQualityScorer:
    """Test QualityScorer functionality."""

    @pytest.fixture
    def mock_ai_provider(self):
        """Create a mock AI provider for testing with pre-configured TestModel."""
        mock_provider = MagicMock()

        def create_agent_mock(output_type, system_prompt):
            # Return appropriate TestModel based on output_type
            if output_type == AIContentQualityResult:
                test_model = TestModel(
                    custom_output_args=AIContentQualityResult(
                        writing_quality=15, informativeness=16, credibility=8, reasoning="Good quality article"
                    )
                )
            else:
                # Default for unknown types
                test_model = TestModel()

            return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

        mock_provider.create_agent = create_agent_mock
        return mock_provider

    @pytest.fixture
    def quality_scorer(self, mock_ai_provider):
        """Create QualityScorer instance for testing with default settings."""
        return QualityScorer(
            ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(quality_scoring_enabled=True)
        )

    @pytest.fixture
    def quality_scorer_disabled(self, mock_ai_provider):
        """Create QualityScorer with AI quality scoring disabled."""
        return QualityScorer(
            ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(quality_scoring_enabled=False)
        )

    @pytest.mark.asyncio
    async def test_metadata_score_calculation(self, quality_scorer_disabled):
        """Test rule-based metadata score calculation."""

        # Complete article: author, published_at, tags, >1000 chars content
        complete_article = Article(
            title="Complete Article",
            url=HttpUrl("https://example.com/test"),
            content="A" * 1200,  # >1000 chars
            author="John Doe",
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
            tags=["ai", "tech"],
        )

        result = await quality_scorer_disabled.calculate_quality_score(complete_article)

        assert result is not None
        # When AI scoring disabled, metadata score is scaled to 0-100
        # Expected: 10 (author) + 10 (date) + 5 (tags) + 15 (>500 chars) + 10 (>1000 chars) = 50
        # Scaled: 50 * 2 = 100
        assert result.quality_score == 100
        assert result.metadata_score == 50
        assert result.ai_content_score == 0

    @pytest.mark.asyncio
    async def test_metadata_score_minimal_article(self, quality_scorer_disabled):
        """Test metadata score for minimal article."""

        # Minimal article: no author, no date, no tags, short content
        minimal_article = Article(
            title="Minimal Article",
            url=HttpUrl("https://example.com/test"),
            content="A" * 300,  # >100 but <500 chars
            fetch_timestamp=datetime.now(UTC),
        )

        result = await quality_scorer_disabled.calculate_quality_score(minimal_article)

        assert result is not None
        # Expected: 0 (no metadata), scaled to 0-100 = 0
        assert result.quality_score == 0
        assert result.metadata_score == 0
        assert result.ai_content_score == 0

    @pytest.mark.asyncio
    async def test_hybrid_quality_scoring_enabled(self, quality_scorer):
        """Test hybrid quality scoring with AI enabled."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            author="John Doe",
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
            tags=["ai"],
        )

        result = await quality_scorer.calculate_quality_score(article)

        assert result is not None
        # Metadata score: 10 (author) + 10 (date) + 5 (tags) + 0 (content <500) = 25
        # AI score from default mock: 15 + 16 + 8 = 39
        # Total: 25 + 39 = 64
        assert result.quality_score == 64
        assert result.metadata_score == 25
        assert result.ai_content_score == 39

    @pytest.mark.asyncio
    async def test_quality_scoring_disabled(self, quality_scorer_disabled):
        """Test that AI quality scoring can be disabled."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="A" * 600,  # >500 chars
            author="John Doe",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await quality_scorer_disabled.calculate_quality_score(article)

        assert result is not None
        # When disabled, metadata score scaled to 0-100
        # Expected: (10 + 15) * 2 = 50
        assert result.quality_score == 50
        assert result.metadata_score == 25
        assert result.ai_content_score == 0
