"""
Tests for Summarizer implementation using PydanticAI
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import Settings
from app.processors.fetchers.base import Article
from app.processors.summarizer import Summarizer, SummaryResult


class TestSummarizer:
    """Test Summarizer functionality."""

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
    def summarizer_brief(self, mock_ai_provider):
        """Create Summarizer instance with 'brief' style for testing."""
        return Summarizer(ai_provider=mock_ai_provider, summary_style="brief")

    @pytest.fixture
    def summarizer_detailed(self, mock_ai_provider):
        """Create Summarizer instance with 'detailed' style for testing."""
        return Summarizer(ai_provider=mock_ai_provider, summary_style="detailed")

    @pytest.fixture
    def summarizer_bullets(self, mock_ai_provider):
        """Create Summarizer instance with 'bullet_points' style for testing."""
        return Summarizer(ai_provider=mock_ai_provider, summary_style="bullet_points")

    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing."""
        fetch_time = datetime.now(UTC)
        return [
            Article(
                title="AI Breakthrough: GPT-5 Achieves Human-Level Reasoning",
                url=HttpUrl("https://example.com/article1"),
                content=(
                    "OpenAI has announced a major breakthrough with the release of GPT-5, a language model that "
                    "achieves human-level reasoning capabilities. The new model demonstrates unprecedented ability "
                    "to understand complex problems, reason through multi-step tasks, and provide accurate solutions. "
                    "Industry experts are calling this a watershed moment in artificial intelligence development. "
                    "The model's performance on standardized reasoning tests exceeded expectations, with scores "
                    "comparable to human professionals in various domains. Researchers attribute the breakthrough "
                    "to novel architectural improvements and advanced training techniques. The implications for "
                    "industries ranging from healthcare to finance are significant, with potential applications "
                    "in diagnosis, decision support, and strategic planning."
                ),
                published_at=datetime(2024, 1, 15, 10, 0),
                fetch_timestamp=fetch_time,
                tags=["AI", "OpenAI", "GPT-5"],
                ai_topics=["Artificial Intelligence", "Machine Learning", "GPT-5"],
            ),
            Article(
                title="Climate Crisis: UN Report Warns of Tipping Points",
                url=HttpUrl("https://example.com/article2"),
                content=(
                    "A comprehensive UN climate report released today warns that several critical climate tipping "
                    "points may be reached sooner than previously predicted. The report, compiled by leading climate "
                    "scientists, highlights accelerating ice sheet collapse in Antarctica and Greenland, rapidly "
                    "warming ocean currents, and unprecedented loss of tropical rainforests. Scientists emphasize "
                    "the urgent need for immediate action to reduce greenhouse gas emissions and implement adaptation "
                    "strategies. The report projects severe impacts on coastal communities, agricultural systems, "
                    "and biodiversity if current trends continue."
                ),
                published_at=datetime(2024, 1, 15, 11, 0),
                fetch_timestamp=fetch_time,
                tags=["climate", "UN", "environment"],
                ai_topics=["Climate Change", "Environmental Science", "UN Report"],
            ),
            Article(
                title="Short Article",
                url=HttpUrl("https://example.com/article3"),
                content="Brief news.",
                published_at=datetime(2024, 1, 15, 9, 0),
                fetch_timestamp=fetch_time,
                tags=[],
            ),
            Article(
                title="Empty Content Article",
                url=HttpUrl("https://example.com/article4"),
                content="",
                published_at=datetime(2024, 1, 15, 9, 0),
                fetch_timestamp=fetch_time,
                tags=[],
            ),
        ]

    @pytest.mark.asyncio
    async def test_summarize_brief_style_success(self, summarizer_brief, sample_articles):
        """Test successful brief summary generation."""
        # Override agent with TestModel
        test_model = TestModel(
            custom_output_args=SummaryResult(
                summary=(
                    "OpenAI's GPT-5 represents a major AI breakthrough, achieving human-level reasoning "
                    "capabilities. The model excels at complex problem-solving and multi-step tasks, "
                    "with implications for healthcare, finance, and other industries."
                ),
                key_points=[
                    "GPT-5 achieves human-level reasoning",
                    "Breakthrough attributed to novel architecture",
                    "Significant implications across industries",
                ],
                reasoning="Focused on core breakthrough and key implications",
            )
        )

        with summarizer_brief.agent.override(model=test_model):
            result = await summarizer_brief.summarize(sample_articles[0])

            assert result.summary is not None
            assert "GPT-5" in result.summary
            assert "human-level reasoning" in result.summary
            assert len(result.summary) > 0

    @pytest.mark.asyncio
    async def test_summarize_detailed_style_success(self, summarizer_detailed, sample_articles):
        """Test successful detailed summary generation."""
        test_model = TestModel(
            custom_output_args=SummaryResult(
                summary=(
                    "OpenAI has announced a significant breakthrough in artificial intelligence with the release "
                    "of GPT-5, a language model that demonstrates human-level reasoning capabilities. The model "
                    "represents a watershed moment in AI development, showing unprecedented ability to understand "
                    "complex problems and provide accurate solutions. Industry experts highlight the model's "
                    "performance on standardized reasoning tests, which exceeded expectations with scores comparable "
                    "to human professionals across various domains. Researchers credit novel architectural improvements "
                    "and advanced training techniques for the breakthrough. The implications span multiple industries, "
                    "including healthcare, finance, and strategic planning, with potential applications in diagnosis "
                    "and decision support systems."
                ),
                key_points=[
                    "GPT-5 achieves human-level reasoning capabilities",
                    "Novel architecture and training techniques drive breakthrough",
                    "Performance comparable to human professionals",
                    "Wide-ranging applications in healthcare and finance",
                ],
                reasoning="Comprehensive overview with context and implications",
            )
        )

        with summarizer_detailed.agent.override(model=test_model):
            result = await summarizer_detailed.summarize(sample_articles[0])

            assert result.summary is not None
            assert len(result.summary) > 200  # Detailed should be longer
            assert "GPT-5" in result.summary
            assert "breakthrough" in result.summary

    @pytest.mark.asyncio
    async def test_summarize_bullet_points_style_success(self, summarizer_bullets, sample_articles):
        """Test successful bullet points summary generation."""
        test_model = TestModel(
            custom_output_args=SummaryResult(
                summary="GPT-5 represents a major AI breakthrough with human-level reasoning capabilities.",
                key_points=[
                    "OpenAI releases GPT-5 with human-level reasoning",
                    "Model excels at complex problem-solving and multi-step tasks",
                    "Performance scores comparable to human professionals",
                    "Novel architecture and training techniques drive success",
                    "Wide applications in healthcare, finance, and strategic planning",
                ],
                reasoning="Organized as actionable bullet points",
            )
        )

        with summarizer_bullets.agent.override(model=test_model):
            result = await summarizer_bullets.summarize(sample_articles[0])

            assert result.summary is not None
            # Bullet points should include bullet markers
            assert "•" in result.summary
            # Should contain multiple points
            assert result.summary.count("•") >= 3

    @pytest.mark.asyncio
    async def test_summarize_with_topics(self, summarizer_brief, sample_articles):
        """Test that summarization uses topics from TopicExtractor when available."""
        test_model = TestModel(
            custom_output_args=SummaryResult(
                summary="UN climate report warns of critical tipping points approaching sooner than expected.",
                key_points=[
                    "Critical climate tipping points approaching",
                    "Accelerating ice sheet collapse",
                    "Urgent action needed to reduce emissions",
                ],
                reasoning="Focused on main warning and key impacts",
            )
        )

        with summarizer_brief.agent.override(model=test_model):
            # Verify topics are included in prompt building
            prompt = summarizer_brief._build_summarization_prompt(sample_articles[1])
            assert "Climate Change" in prompt
            assert "Environmental Science" in prompt
            assert "UN Report" in prompt

            result = await summarizer_brief.summarize(sample_articles[1])
            assert result.summary is not None

    @pytest.mark.asyncio
    async def test_summarize_minimal_content_fallback(self, summarizer_brief, sample_articles):
        """Test handling of article with minimal content - uses excerpt instead of AI."""
        result = await summarizer_brief.summarize(sample_articles[2])

        # Should have summary (excerpt from content)
        assert result.summary is not None
        assert "Brief news" in result.summary

    @pytest.mark.asyncio
    async def test_summarize_empty_content_fallback(self, summarizer_brief, sample_articles):
        """Test handling of article with empty content - uses title as fallback."""
        result = await summarizer_brief.summarize(sample_articles[3])

        # Should have summary (title as fallback)
        assert result.summary is not None
        assert "Empty Content Article" in result.summary

    @pytest.mark.asyncio
    async def test_summarize_ai_error_handling(self, summarizer_brief, sample_articles):
        """Test that AI errors are handled gracefully with content excerpt fallback."""
        # Make agent raise an exception
        with patch.object(summarizer_brief.agent, "run", side_effect=Exception("AI service error")):
            result = await summarizer_brief.summarize(sample_articles[0])

            # Should have summary (fallback to content excerpt)
            assert result.summary is not None
            # Should contain part of original content
            assert len(result.summary) > 0

    @pytest.mark.asyncio
    async def test_summarize_content_truncation(self, summarizer_brief):
        """Test that very long content is truncated to avoid token limits."""
        # Create article with very long content
        long_content = "A " * 5000  # 10,000 characters
        article = Article(
            title="Long Article",
            url=HttpUrl("https://example.com/long"),
            content=long_content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
            tags=[],
        )

        test_model = TestModel(
            custom_output_args=SummaryResult(summary="Test summary", key_points=["Point 1"], reasoning="Test reasoning")
        )

        with summarizer_brief.agent.override(model=test_model):
            # Mock the agent.run to capture the prompt
            original_run = summarizer_brief.agent.run

            async def mock_run(prompt):
                # Verify content was truncated to summary_content_length (default 2000)
                assert "Content:" in prompt
                content_start = prompt.find("Content:") + len("Content:")
                content_end = prompt.find("\n\nCreate a", content_start)
                content_in_prompt = prompt[content_start:content_end].strip()
                # Content should be truncated to 2000 chars
                assert len(content_in_prompt) <= 2000
                return await original_run(prompt)

            with patch.object(summarizer_brief.agent, "run", side_effect=mock_run):
                await summarizer_brief.summarize(article)

    @pytest.mark.asyncio
    async def test_summary_result_model_validation(self):
        """Test SummaryResult Pydantic model validation."""
        # Valid result
        result = SummaryResult(
            summary="This is a test summary of the article.",
            key_points=["Point 1", "Point 2", "Point 3"],
            reasoning="Summary focuses on main ideas",
        )

        assert result.summary == "This is a test summary of the article."
        assert len(result.key_points) == 3
        assert result.reasoning == "Summary focuses on main ideas"

        # Empty key points should be valid
        result_empty = SummaryResult(summary="Summary", key_points=[], reasoning="No key points")
        assert result_empty.key_points == []

    def test_build_system_prompt_brief(self, summarizer_brief):
        """Test that brief style system prompt is built correctly."""
        prompt = summarizer_brief._build_system_prompt()

        assert "expert at summarizing" in prompt
        assert "Brief" in prompt
        assert "1-2 paragraphs" in prompt
        assert "concise" in prompt

    def test_build_system_prompt_detailed(self, summarizer_detailed):
        """Test that detailed style system prompt is built correctly."""
        prompt = summarizer_detailed._build_system_prompt()

        assert "expert at summarizing" in prompt
        assert "Detailed" in prompt
        assert "3-4 paragraphs" in prompt
        assert "comprehensive" in prompt

    def test_build_system_prompt_bullet_points(self, summarizer_bullets):
        """Test that bullet points style system prompt is built correctly."""
        prompt = summarizer_bullets._build_system_prompt()

        assert "expert at summarizing" in prompt
        assert "Bullet Points" in prompt
        assert "list of key points" in prompt

    def test_build_summarization_prompt(self, summarizer_brief, sample_articles):
        """Test that summarization prompt is built correctly."""
        prompt = summarizer_brief._build_summarization_prompt(sample_articles[0])

        assert sample_articles[0].title in prompt
        assert "OpenAI has announced" in prompt  # Part of content
        assert "Create a brief summary" in prompt

    def test_build_summarization_prompt_with_tags(self, summarizer_brief, sample_articles):
        """Test prompt includes tags when available."""
        prompt = summarizer_brief._build_summarization_prompt(sample_articles[0])

        assert "AI" in prompt
        assert "OpenAI" in prompt
        assert "GPT-5" in prompt

    def test_build_summarization_prompt_without_tags(self, summarizer_brief, sample_articles):
        """Test prompt handles articles without tags."""
        prompt = summarizer_brief._build_summarization_prompt(sample_articles[2])

        assert "Tags: None" in prompt

    @pytest.mark.asyncio
    async def test_custom_summary_length_setting(self, mock_ai_provider, sample_articles):
        """Test that custom summary length setting is respected in system prompt."""
        # Create settings with custom summary length
        custom_settings = Settings(
            database_url="postgresql://test",
            secret_key="test-secret",
            summary_max_length=300,  # Custom limit
        )

        summarizer = Summarizer(settings=custom_settings, ai_provider=mock_ai_provider, summary_style="brief")

        # Check system prompt contains custom length
        system_prompt = summarizer._build_system_prompt()
        assert "300 words" in system_prompt

    @pytest.mark.asyncio
    async def test_summarize_multiple_articles_independently(self, summarizer_brief, sample_articles):
        """Test that summarization works independently for multiple articles."""
        test_model_1 = TestModel(
            custom_output_args=SummaryResult(
                summary="GPT-5 breakthrough summary", key_points=["Point 1"], reasoning="AI article"
            )
        )

        test_model_2 = TestModel(
            custom_output_args=SummaryResult(
                summary="Climate crisis summary", key_points=["Point 1"], reasoning="Climate article"
            )
        )

        with summarizer_brief.agent.override(model=test_model_1):
            result_1 = await summarizer_brief.summarize(sample_articles[0])

        with summarizer_brief.agent.override(model=test_model_2):
            result_2 = await summarizer_brief.summarize(sample_articles[1])

        # Each article should have its own summary
        assert "GPT-5" in result_1.summary
        assert "Climate" in result_2.summary
        # Summaries should not interfere with each other
        assert "Climate" not in result_1.summary
        assert "GPT-5" not in result_2.summary

    @pytest.mark.asyncio
    async def test_summarize_returns_original_article_on_error(self, summarizer_brief, sample_articles):
        """Test that errors return the article with fallback summary, not None."""
        with patch.object(summarizer_brief.agent, "run", side_effect=RuntimeError("AI failure")):
            result = await summarizer_brief.summarize(sample_articles[0])

            # Should return the article, not None
            assert result is not None
            assert isinstance(result, Article)
            assert result.summary is not None
            # Should have fallback excerpt
            assert len(result.summary) > 0
