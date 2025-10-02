"""
Tests for TopicExtractor implementation using PydanticAI
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import Settings
from app.processors.fetchers.base import Article
from app.processors.topic_extractor import TopicExtractionResult, TopicExtractor


class TestTopicExtractor:
    """Test TopicExtractor functionality."""

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
    def topic_extractor(self, mock_ai_provider):
        """Create TopicExtractor instance for testing."""
        return TopicExtractor(ai_provider=mock_ai_provider)

    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing."""
        return [
            Article(
                title="OpenAI Launches GPT-5 with Revolutionary Features",
                url=HttpUrl("https://example.com/article1"),
                content=(
                    "OpenAI has announced the release of GPT-5, their latest language model with groundbreaking "
                    "capabilities. The new model features improved reasoning, better context handling, and multimodal "
                    "understanding. Industry experts are calling it a significant leap forward in artificial "
                    "intelligence technology."
                ),
                published_at=datetime(2024, 1, 15, 10, 0),
                tags=["AI", "OpenAI", "GPT"],
            ),
            Article(
                title="Climate Change: Scientists Warn of Rising Sea Levels",
                url=HttpUrl("https://example.com/article2"),
                content=(
                    "A new study published in Nature Climate Change reveals alarming projections about sea level rise. "
                    "Researchers from leading institutions warn that coastal cities face unprecedented risks. "
                    "The study calls for immediate action to reduce greenhouse gas emissions and adapt infrastructure."
                ),
                published_at=datetime(2024, 1, 15, 11, 0),
                tags=["climate", "science"],
            ),
            Article(
                title="Minimal Content Article",
                url=HttpUrl("https://example.com/article3"),
                content="Short.",
                published_at=datetime(2024, 1, 15, 9, 0),
                tags=[],
            ),
            Article(
                title="Empty Content Article",
                url=HttpUrl("https://example.com/article4"),
                content="",
                published_at=datetime(2024, 1, 15, 9, 0),
                tags=[],
            ),
        ]

    @pytest.mark.asyncio
    async def test_extract_topics_success(self, topic_extractor, sample_articles):
        """Test successful topic extraction from article."""
        # Override agent with TestModel
        test_model = TestModel(
            custom_output_args=TopicExtractionResult(
                topics=["GPT-5", "OpenAI", "Artificial Intelligence", "Language Models"],
                reasoning="Article focuses on the GPT-5 release and AI technology advancements",
            )
        )

        with topic_extractor.agent.override(model=test_model):
            topics = await topic_extractor.extract_topics(sample_articles[0])

            assert len(topics) == 4
            assert "GPT-5" in topics
            assert "OpenAI" in topics
            assert "Artificial Intelligence" in topics
            assert "Language Models" in topics

    @pytest.mark.asyncio
    async def test_extract_topics_max_limit_enforced(self, topic_extractor, sample_articles):
        """Test that max topics limit is enforced even if AI returns more."""
        # Override agent with TestModel that returns more than max topics (default 5)
        test_model = TestModel(
            custom_output_args=TopicExtractionResult(
                topics=[
                    "Topic1",
                    "Topic2",
                    "Topic3",
                    "Topic4",
                    "Topic5",
                    "Topic6",
                    "Topic7",
                ],  # 7 topics
                reasoning="Many topics identified",
            )
        )

        with topic_extractor.agent.override(model=test_model):
            topics = await topic_extractor.extract_topics(sample_articles[0])

            # Should only return first 5 topics (max limit)
            assert len(topics) <= topic_extractor.settings.topic_extraction_max_topics
            assert len(topics) == 5

    @pytest.mark.asyncio
    async def test_extract_topics_minimal_content(self, topic_extractor, sample_articles):
        """Test handling of article with minimal content."""
        # Article with very short content should return empty list
        topics = await topic_extractor.extract_topics(sample_articles[2])

        assert topics == []

    @pytest.mark.asyncio
    async def test_extract_topics_empty_content(self, topic_extractor, sample_articles):
        """Test handling of article with empty content."""
        # Article with empty content should return empty list
        topics = await topic_extractor.extract_topics(sample_articles[3])

        assert topics == []

    @pytest.mark.asyncio
    async def test_extract_topics_ai_error_handling(self, topic_extractor, sample_articles):
        """Test that errors during topic extraction are handled gracefully."""
        # Make agent raise an exception
        with patch.object(topic_extractor.agent, "run", side_effect=Exception("AI service error")):
            topics = await topic_extractor.extract_topics(sample_articles[0])

            # Should return empty list on error
            assert topics == []

    @pytest.mark.asyncio
    async def test_extract_topics_different_content_types(self, topic_extractor, sample_articles):
        """Test topic extraction from different content types."""
        # Test climate change article
        test_model = TestModel(
            custom_output_args=TopicExtractionResult(
                topics=["Climate Change", "Sea Level Rise", "Environmental Science"],
                reasoning="Article discusses climate science and environmental impacts",
            )
        )

        with topic_extractor.agent.override(model=test_model):
            topics = await topic_extractor.extract_topics(sample_articles[1])

            assert "Climate Change" in topics
            assert "Sea Level Rise" in topics
            assert "Environmental Science" in topics

    @pytest.mark.asyncio
    async def test_topic_extraction_result_model_validation(self):
        """Test TopicExtractionResult Pydantic model validation."""
        # Valid result
        result = TopicExtractionResult(topics=["Topic1", "Topic2", "Topic3"], reasoning="These are the main topics")

        assert len(result.topics) == 3
        assert result.reasoning == "These are the main topics"

        # Empty topics list should be valid
        result_empty = TopicExtractionResult(topics=[], reasoning="No clear topics found")
        assert result_empty.topics == []

    def test_build_extraction_prompt(self, topic_extractor, sample_articles):
        """Test that extraction prompt is built correctly."""
        prompt = topic_extractor._build_extraction_prompt(sample_articles[0])

        assert sample_articles[0].title in prompt
        assert "OpenAI has announced" in prompt  # Part of content
        assert "Extract the key topics and themes" in prompt

    def test_build_extraction_prompt_with_tags(self, topic_extractor, sample_articles):
        """Test prompt includes tags when available."""
        prompt = topic_extractor._build_extraction_prompt(sample_articles[0])

        assert "AI" in prompt
        assert "OpenAI" in prompt
        assert "GPT" in prompt

    def test_build_extraction_prompt_without_tags(self, topic_extractor, sample_articles):
        """Test prompt handles articles without tags."""
        prompt = topic_extractor._build_extraction_prompt(sample_articles[2])

        assert "Tags: None" in prompt

    @pytest.mark.asyncio
    async def test_extract_topics_truncates_long_content(self, topic_extractor):
        """Test that very long content is truncated to avoid token limits."""
        # Create article with very long content
        long_content = "A " * 2000  # 4000 characters
        article = Article(
            title="Long Article",
            url=HttpUrl("https://example.com/long"),
            content=long_content,
            published_at=datetime(2024, 1, 15, 10, 0),
            tags=[],
        )

        test_model = TestModel(custom_output_args=TopicExtractionResult(topics=["Topic1"], reasoning="Test reasoning"))

        with topic_extractor.agent.override(model=test_model):
            # Mock the agent.run to capture the prompt
            original_run = topic_extractor.agent.run

            async def mock_run(prompt):
                # Verify content was truncated to 1000 chars
                assert "Content:" in prompt
                content_start = prompt.find("Content:") + len("Content:")
                content_end = prompt.find("Tags:", content_start)
                content_in_prompt = prompt[content_start:content_end].strip()
                # Content should be truncated to 1000 chars
                assert len(content_in_prompt) <= 1000
                return await original_run(prompt)

            with patch.object(topic_extractor.agent, "run", side_effect=mock_run):
                await topic_extractor.extract_topics(article)

    @pytest.mark.asyncio
    async def test_extract_topics_returns_empty_on_ai_failure(self, topic_extractor, sample_articles):
        """Test that AI failures are handled gracefully without breaking the pipeline."""
        # Simulate various AI failures
        with patch.object(topic_extractor.agent, "run", side_effect=TimeoutError("AI timeout")):
            topics = await topic_extractor.extract_topics(sample_articles[0])
            assert topics == []

        with patch.object(topic_extractor.agent, "run", side_effect=ValueError("Invalid response")):
            topics = await topic_extractor.extract_topics(sample_articles[0])
            assert topics == []

    @pytest.mark.asyncio
    async def test_custom_max_topics_setting(self, mock_ai_provider, sample_articles):
        """Test that custom max_topics setting is respected."""

        # Create settings with custom max topics
        custom_settings = Settings(
            database_url="postgresql://test",
            secret_key="test-secret",
            topic_extraction_max_topics=3,  # Custom limit
        )

        extractor = TopicExtractor(settings=custom_settings, ai_provider=mock_ai_provider)

        # AI returns 5 topics
        test_model = TestModel(
            custom_output_args=TopicExtractionResult(
                topics=["Topic1", "Topic2", "Topic3", "Topic4", "Topic5"], reasoning="Five topics"
            )
        )

        with extractor.agent.override(model=test_model):
            topics = await extractor.extract_topics(sample_articles[0])

            # Should only return 3 topics due to custom setting
            assert len(topics) == 3
            assert topics == ["Topic1", "Topic2", "Topic3"]

    @pytest.mark.asyncio
    async def test_extract_topics_with_whitespace_content(self, topic_extractor):
        """Test handling of article with only whitespace content."""
        article = Article(
            title="Whitespace Article",
            url=HttpUrl("https://example.com/whitespace"),
            content="   \n\t  \n   ",  # Only whitespace
            published_at=datetime(2024, 1, 15, 10, 0),
            tags=[],
        )

        topics = await topic_extractor.extract_topics(article)
        assert topics == []

    @pytest.mark.asyncio
    async def test_extract_topics_multiple_articles_independently(self, topic_extractor, sample_articles):
        """Test that topic extraction works independently for multiple articles."""
        test_model_1 = TestModel(
            custom_output_args=TopicExtractionResult(topics=["AI", "GPT-5"], reasoning="AI article")
        )

        test_model_2 = TestModel(
            custom_output_args=TopicExtractionResult(topics=["Climate", "Science"], reasoning="Climate article")
        )

        with topic_extractor.agent.override(model=test_model_1):
            topics_1 = await topic_extractor.extract_topics(sample_articles[0])

        with topic_extractor.agent.override(model=test_model_2):
            topics_2 = await topic_extractor.extract_topics(sample_articles[1])

        # Each article should have its own topics
        assert topics_1 == ["AI", "GPT-5"]
        assert topics_2 == ["Climate", "Science"]
        # Topics should not interfere with each other
        assert "AI" not in topics_2
        assert "Climate" not in topics_1
