"""
Topic extraction service using PydanticAI.

This module provides AI-powered topic extraction to identify key themes and subjects
in articles for content categorization and relevance scoring.
"""

import textwrap

from loguru import logger
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article


class TopicExtractionResult(BaseModel):
    """AI-extracted topics with reasoning."""

    topics: list[str] = Field(description="List of key topics or themes extracted from the article")
    reasoning: str = Field(description="Brief explanation of why these topics were identified")


class TopicExtractor:
    """
    Extracts key topics from articles using PydanticAI.

    This class uses AI-powered analysis to identify the main themes, subjects,
    and categories in article content. The AI provider is configurable through
    application settings.
    """

    def __init__(self, settings: Settings | None = None, ai_provider: AIProvider | None = None):
        """
        Initialize the topic extractor with PydanticAI agent.

        Args:
            settings: Application settings (uses get_settings() if not provided)
            ai_provider: AI provider instance (creates from settings if not provided)
        """
        self.settings = settings or get_settings()

        # Create AI provider if not injected
        provider = ai_provider or create_ai_provider(self.settings)

        # Initialize PydanticAI agent using the provider
        self.agent = provider.create_agent(
            output_type=TopicExtractionResult,
            system_prompt=(
                "You are an expert at analyzing articles and extracting key topics and themes. "
                "Your task is to identify the main subjects, themes, and categories that best "
                "represent the article's content.\n\n"
                "Guidelines:\n"
                f"1. Extract {self.settings.topic_extraction_max_topics} or fewer distinct topics\n"
                "2. Focus on specific, meaningful topics rather than generic categories\n"
                "3. Use concise phrases (1-3 words per topic)\n"
                "4. Prioritize topics that would help with content categorization and relevance matching\n"
                "5. Consider entities (people, organizations, places), concepts, technologies, and events\n"
                "6. Avoid overly broad topics unless they are the primary focus"
            ),
        )

    async def extract_topics(self, article: Article) -> list[str]:
        """
        Extract key topics from an article using AI.

        Args:
            article: Article to extract topics from

        Returns:
            List of extracted topics (empty list on error)
        """
        # Handle minimal content
        if not article.content or len(article.content.strip()) < 50:
            logger.debug(f"Article '{article.title[:50]}...' has insufficient content for topic extraction")
            return []

        # Prepare extraction prompt
        prompt = self._build_extraction_prompt(article)

        try:
            # Run AI extraction
            result = await self.agent.run(prompt)
            extraction_result = result.output

            # Enforce max topics limit
            topics = extraction_result.topics[: self.settings.topic_extraction_max_topics]

            logger.debug(f"Extracted topics for '{article.title[:50]}...': {topics} - {extraction_result.reasoning}")

            return topics

        except Exception as e:
            logger.error(f"Error extracting topics from article '{article.title[:50]}...': {e}")
            # On error, return empty list to avoid breaking the pipeline
            return []

    def _build_extraction_prompt(self, article: Article) -> str:
        """Build prompt for AI topic extraction."""
        # Truncate content to avoid token limits (use first 1000 chars)
        content = article.content[:1000] if article.content else ""

        return textwrap.dedent(f"""\
            Article Title: {article.title}
            Content: {content}
            Tags: {", ".join(article.tags) if article.tags else "None"}

            Extract the key topics and themes from this article.
        """)
