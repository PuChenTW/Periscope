"""
Tests for ContentNormalizer implementation
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import Settings
from app.processors.fetchers.base import Article
from app.processors.normalizer import ContentNormalizer, SpamDetectionResult


class TestContentNormalizer:
    """Test ContentNormalizer functionality."""

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
    def normalizer(self, mock_ai_provider):
        """Create ContentNormalizer instance for testing."""
        return ContentNormalizer(ai_provider=mock_ai_provider)

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
            author="John Doe",
            tags=["AI", "OpenAI", "GPT"],
        )

    @pytest.mark.asyncio
    async def test_normalize_valid_article(self, normalizer, valid_article):
        """Test normalization of a complete, valid article."""
        # Mock AI to return not spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=False, confidence=0.95, reasoning="Legitimate news article about technology"
            )
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(valid_article)

        assert result is not None
        assert result.title == valid_article.title
        assert result.content == valid_article.content

    @pytest.mark.asyncio
    async def test_normalize_empty_content(self, normalizer):
        """Test rejection of article with empty content."""
        article = Article(
            title="Empty Content Article",
            url=HttpUrl("https://example.com/empty"),
            content="",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_whitespace_only_content(self, normalizer):
        """Test rejection of article with only whitespace content."""
        article = Article(
            title="Whitespace Article",
            url=HttpUrl("https://example.com/whitespace"),
            content="   \n\t  \n   ",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_content_too_short(self, normalizer):
        """Test rejection of article with content below minimum length."""
        article = Article(
            title="Short Article",
            url=HttpUrl("https://example.com/short"),
            content="Short.",  # Only 6 characters, below 100 char minimum
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_content_exactly_minimum_length(self, normalizer):
        """Test article with exactly minimum content length is accepted."""
        # Create content that is exactly 100 characters (realistic text to avoid spam detection)
        content = "The quick brown fox jumps over the lazy dog while scientists observe animal behavior patterns today."

        article = Article(
            title="Minimum Length Article",
            url=HttpUrl("https://example.com/min"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        # Mock AI to return not spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(is_spam=False, confidence=0.90, reasoning="Valid article content")
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.content.strip()) == 100

    @pytest.mark.asyncio
    async def test_normalize_content_just_below_minimum(self, normalizer):
        """Test article with content just below minimum is rejected."""
        # 99 characters - just below minimum
        content = "A" * 99

        article = Article(
            title="Below Minimum Article",
            url=HttpUrl("https://example.com/below"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_with_unicode_content(self, normalizer):
        """Test handling of unicode characters in content."""
        content = (
            "这是一篇关于人工智能的文章。AI技术正在快速发展，影响着我们的日常生活。"  # noqa: RUF001
            "机器学习和深度学习是当前最热门的研究方向。专家预测，未来十年AI将带来重大变革。"  # noqa: RUF001
            "This article discusses artificial intelligence and its impact on society."
        )

        article = Article(
            title="AI Article with Unicode",
            url=HttpUrl("https://example.com/unicode"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        # Mock AI to return not spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=False, confidence=0.85, reasoning="Legitimate multi-language article"
            )
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(article)

        assert result is not None

    @pytest.mark.asyncio
    async def test_normalize_with_emojis(self, normalizer):
        """Test handling of emoji characters in content."""
        content = (
            "Technology companies are innovating rapidly 🚀. The new AI models show impressive capabilities 🤖. "
            "Researchers are excited about the potential applications 💡. This could transform many industries ⚡. "
            "The future looks bright for artificial intelligence and machine learning technologies worldwide."
        )

        article = Article(
            title="Tech Article with Emojis",
            url=HttpUrl("https://example.com/emoji"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        # Mock AI to return not spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=False, confidence=0.82, reasoning="Casual but legitimate tech article"
            )
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(article)

        assert result is not None

    @pytest.mark.asyncio
    async def test_custom_min_length_setting(self, mock_ai_provider):
        """Test that custom minimum length setting is respected."""
        normalizer = ContentNormalizer(
            content_min_length=200,  # Custom minimum length
            ai_provider=mock_ai_provider,
        )

        # Content with 150 characters (below custom minimum)
        content = "This is a test article with content that is exactly one hundred and fifty characters long for testing custom minimum length settings properly here."

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(article)
        assert result is None  # Should be rejected with custom 200 char minimum

    @pytest.mark.asyncio
    async def test_spam_detection_enabled(self, normalizer):
        """Test spam detection for excessive uppercase content."""
        # Create content with >70% uppercase letters
        spam_content = "BUY NOW!!! THIS IS AN AMAZING DEAL!!! " * 10

        article = Article(
            title="Spam Article",
            url=HttpUrl("https://example.com/spam"),
            content=spam_content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        # Mock AI to return spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=True, confidence=0.98, reasoning="Excessive uppercase and promotional language"
            )
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(article)

        assert result is None

    @pytest.mark.asyncio
    async def test_spam_detection_disabled(self, mock_ai_provider):
        """Test that spam detection can be disabled via settings."""
        normalizer = ContentNormalizer(
            spam_detection_enabled=False,  # Disable spam detection
            ai_provider=mock_ai_provider,
        )

        # Create obvious spam content
        spam_content = "BUY NOW!!! CLICK HERE!!! " * 20

        article = Article(
            title="Spam Article",
            url=HttpUrl("https://example.com/spam"),
            content=spam_content,
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(article)
        # Should NOT be rejected since spam detection is disabled
        assert result is not None

    @pytest.mark.asyncio
    async def test_normalize_article_with_minimal_metadata(self, normalizer):
        """Test normalization of article with only required fields."""
        article = Article(
            title="Minimal Article",
            url=HttpUrl("https://example.com/minimal"),
            content=(
                "This is a minimal article with just enough content to pass validation. "
                "It has realistic text to avoid spam detection patterns during testing."
            ),
        )

        # Mock AI to return not spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=False, confidence=0.75, reasoning="Simple but legitimate content"
            )
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(article)

        assert result is not None
        assert result.title == "Minimal Article"
        assert result.author is None
        assert result.published_at is None
        assert result.tags == []

    @pytest.mark.asyncio
    async def test_normalize_preserves_article_fields(self, normalizer, valid_article):
        """Test that normalization preserves all article fields."""
        # Mock AI to return not spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(is_spam=False, confidence=0.93, reasoning="Legitimate article")
        )

        with normalizer.agent.override(model=test_model):
            result = await normalizer.normalize(valid_article)

        assert result is not None
        assert result.title == valid_article.title
        assert result.url == valid_article.url
        assert result.content == valid_article.content
        assert result.author == valid_article.author
        assert result.published_at == valid_article.published_at
        assert result.tags == valid_article.tags
        assert result.summary == valid_article.summary
        assert result.ai_topics == valid_article.ai_topics
        assert result.metadata == valid_article.metadata
