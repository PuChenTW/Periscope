"""
Tests for ContentValidator implementation
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import ContentNormalizationSettings
from app.processors.fetchers.base import Article
from app.processors.validator import ContentValidator, SpamDetectionResult


class TestContentValidator:
    """Test ContentValidator functionality."""

    @pytest.fixture
    def mock_ai_provider(self):
        """Create a mock AI provider for testing with pre-configured TestModel based on output_type."""
        mock_provider = MagicMock()

        def create_agent_mock(output_type, system_prompt):
            # Return appropriate TestModel based on output_type for realistic default behavior
            if output_type == SpamDetectionResult:
                test_model = TestModel(
                    custom_output_args=SpamDetectionResult(is_spam=False, confidence=0.9, reasoning="Valid article")
                )
            else:
                # Default for unknown types
                test_model = TestModel()

            return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

        mock_provider.create_agent = create_agent_mock
        return mock_provider

    @pytest.fixture
    def validator(self, mock_ai_provider):
        """Create ContentValidator instance for testing with default settings."""
        return ContentValidator(ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(min_length=50))

    @pytest.fixture
    def validator_no_spam(self, mock_ai_provider):
        """Create ContentValidator with spam detection disabled."""
        return ContentValidator(
            ai_provider=mock_ai_provider,
            settings=ContentNormalizationSettings(min_length=50, spam_detection_enabled=False),
        )

    @pytest.fixture
    def valid_article(self):
        """Create a valid article for testing."""
        return Article(
            title="OpenAI Launches GPT-5 with Revolutionary Features",
            url=HttpUrl("https://example.com/article1"),
            content=(
                "OpenAI has announced the release of GPT-5, their latest language model with groundbreaking "
                "capabilities. The new model features improved reasoning, better context handling, and multimodal "
                "understanding. Industry experts are calling it a significant leap forward in artificial "
                "intelligence technology. This represents a major milestone in AI development."
            ),
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
            author="John Doe",
            tags=["AI", "OpenAI", "GPT"],
        )

    @pytest.mark.asyncio
    async def test_validate_valid_article(self, validator, valid_article):
        """Test validation of a complete, valid article."""
        result = await validator.validate_article(valid_article)

        assert result.is_empty is False
        assert result.is_too_short is False
        assert result.is_spam is False
        assert result.validation_message == "Valid"

    @pytest.mark.asyncio
    async def test_validate_empty_content(self, validator):
        """Test rejection of article with empty content."""
        article = Article(
            title="Empty Content Article",
            url=HttpUrl("https://example.com/empty"),
            content="",
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await validator.validate_article(article)

        assert result.is_empty is True
        assert result.is_too_short is False
        assert result.is_spam is False
        assert "empty" in result.validation_message.lower()

    @pytest.mark.asyncio
    async def test_validate_whitespace_only_content(self, validator):
        """Test rejection of article with only whitespace content."""
        article = Article(
            title="Whitespace Article",
            url=HttpUrl("https://example.com/whitespace"),
            content="   \n\t  \n   ",
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await validator.validate_article(article)

        assert result.is_empty is True
        assert result.is_too_short is False
        assert result.is_spam is False
        assert "empty" in result.validation_message.lower()

    @pytest.mark.asyncio
    async def test_validate_content_too_short(self, validator):
        """Test rejection of article with content below minimum length."""
        article = Article(
            title="Short Article",
            url=HttpUrl("https://example.com/short"),
            content="Short.",  # Only 6 characters, below 50 char minimum
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await validator.validate_article(article)

        assert result.is_empty is False
        assert result.is_too_short is True
        assert result.is_spam is False
        assert "too short" in result.validation_message.lower()

    @pytest.mark.asyncio
    async def test_validate_content_exactly_minimum_length(self, validator):
        """Test article with exactly minimum content length is accepted."""
        # Create content that is exactly 50 characters (realistic text to avoid spam detection)
        content = "The quick brown fox jumps over the lazy doggggggg."
        assert len(content.strip()) == 50

        article = Article(
            title="Minimum Length Article",
            url=HttpUrl("https://example.com/min"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await validator.validate_article(article)

        assert result.is_empty is False
        assert result.is_too_short is False
        assert result.is_spam is False
        assert result.validation_message == "Valid"

    @pytest.mark.asyncio
    async def test_spam_detection_enabled(self, validator):
        """Test spam detection for excessive uppercase content."""
        # Create content with promotional spam
        spam_content = "BUY NOW!!! THIS IS AN AMAZING DEAL!!! " * 10

        article = Article(
            title="Spam Article",
            url=HttpUrl("https://example.com/spam"),
            content=spam_content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        # Mock AI to return spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=True, confidence=0.98, reasoning="Excessive uppercase and promotional language"
            )
        )

        with validator.spam_agent.override(model=test_model):
            result = await validator.validate_article(article)

        assert result.is_empty is False
        assert result.is_too_short is False
        assert result.is_spam is True
        assert result.confidence == 1.0
        assert "spam" in result.validation_message.lower()

    @pytest.mark.asyncio
    async def test_spam_detection_disabled(self, validator_no_spam):
        """Test that spam detection can be disabled via settings."""
        # Create obvious spam content
        spam_content = "BUY NOW!!! CLICK HERE!!! " * 20

        article = Article(
            title="Spam Article",
            url=HttpUrl("https://example.com/spam"),
            content=spam_content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await validator_no_spam.validate_article(article)

        # Should NOT be marked as spam since spam detection is disabled
        assert result.is_empty is False
        assert result.is_too_short is False
        assert result.is_spam is False
        assert result.validation_message == "Valid"
