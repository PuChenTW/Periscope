"""
Article summarization service using PydanticAI.

This module provides AI-powered article summarization to generate concise,
user-friendly summaries for the daily digest. Supports multiple summary styles
and configurable length limits.
"""

import textwrap

from loguru import logger
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article
from app.utils.prompt_validator import sanitize_prompt, validate_prompt_with_ai, validate_summary_prompt


class SummaryResult(BaseModel):
    """AI-generated summary with key points."""

    summary: str = Field(description="Concise summary of the article content")
    key_points: list[str] = Field(description="3-5 key points or takeaways from the article")
    reasoning: str = Field(description="Brief explanation of the summarization approach")


class Summarizer:
    """
    Generates article summaries using PydanticAI.

    This class uses AI-powered analysis to create concise, user-friendly summaries
    of article content. The AI provider is configurable through application settings,
    and summary style can be customized per user preferences.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        ai_provider: AIProvider | None = None,
        summary_style: str = "brief",
        custom_prompt: str | None = None,
    ):
        """
        Initialize the summarizer with PydanticAI agent.

        Args:
            settings: Application settings (uses get_settings() if not provided)
            ai_provider: AI provider instance (creates from settings if not provided)
            summary_style: Summary style - "brief", "detailed", or "bullet_points" (default: "brief")
            custom_prompt: Optional user-defined custom prompt (validated for safety)
        """
        self.settings = settings or get_settings()
        self.summary_style = summary_style

        # Store provider + raw prompt for lazy initialization
        self.ai_provider = ai_provider or create_ai_provider(self.settings)
        self._raw_custom_prompt = custom_prompt

        self.custom_prompt: str | None = None
        self.agent = None
        self._prepared = False

    async def prepare(self) -> None:
        """Lazily prepare AI agent and validate custom prompts."""
        if self._prepared:
            return

        self.custom_prompt = await self._validate_and_sanitize_custom_prompt(self._raw_custom_prompt)

        system_prompt = self._build_system_prompt()
        self.agent = self.ai_provider.create_agent(
            output_type=SummaryResult,
            system_prompt=system_prompt,
        )

        self._prepared = True

    async def _validate_and_sanitize_custom_prompt(self, prompt: str | None) -> str | None:
        """
        Validate and sanitize a custom user prompt.

        Args:
            prompt: User-provided custom prompt

        Returns:
            Sanitized prompt if valid, None if validation fails
        """
        if not prompt:
            return None

        if not self.settings.custom_prompt_validation_enabled:
            logger.warning("Custom prompt validation is disabled - using prompt as-is")
            return sanitize_prompt(prompt)

        # Layer 1: Pattern-based validation
        is_valid, error_message = validate_summary_prompt(
            prompt,
            min_length=self.settings.custom_prompt_min_length,
            max_length=self.settings.custom_prompt_max_length,
        )

        if not is_valid:
            logger.warning(f"Custom prompt validation failed: {error_message}. Falling back to default prompts.")
            return None

        # Layer 2: AI-powered validation (optional)
        if self.settings.ai_prompt_validation_enabled:
            ai_is_safe, confidence, reasoning = await validate_prompt_with_ai(
                prompt=prompt,
                settings=self.settings,
                ai_provider=self.ai_provider,
            )

            if not ai_is_safe:
                logger.warning(
                    "Custom prompt rejected by AI guard (confidence {:.2f}): {}. Falling back to default prompts.",
                    confidence,
                    reasoning,
                )
                return None

            logger.info("Custom prompt passed AI guard (confidence {:.2f}): {}", confidence, reasoning)

        sanitized = sanitize_prompt(prompt)
        logger.info("Custom prompt validated and sanitized: '{}...'", sanitized[:50])
        return sanitized

    def _build_system_prompt(self) -> str:
        """Build system prompt based on summary style and custom prompt."""
        base_prompt = textwrap.dedent("""\
            You are an expert at summarizing articles for busy readers.
            Your task is to create clear, concise, and accurate summaries that capture
            the essence of the article while being easy to understand.

            Guidelines:
            - Focus on the main ideas and key information
            - Use clear, accessible language
            - Maintain factual accuracy
            - Avoid unnecessary details or tangents
            - Extract 3-5 key points or takeaways
        """)

        style_guidelines = {
            "brief": textwrap.dedent(f"""\
                Summary Style: Brief (1-2 paragraphs, max {self.settings.summary_max_length} words)
                - Focus on the core message
                - Keep it concise and to the point
                - Use simple, clear sentences
            """),
            "detailed": textwrap.dedent(f"""\
                Summary Style: Detailed (3-4 paragraphs, max {self.settings.summary_max_length} words)
                - Provide comprehensive overview
                - Include important context and background
                - Cover multiple aspects of the topic
                - Explain technical terms if needed
            """),
            "bullet_points": textwrap.dedent(f"""\
                Summary Style: Bullet Points (max {self.settings.summary_max_length} words total)
                - Create a list of key points
                - Each point should be clear and self-contained
                - Use concise, action-oriented language
                - Organize points in order of importance
            """),
        }

        style_guide = style_guidelines.get(self.summary_style, style_guidelines["brief"])

        # Build the complete system prompt
        prompt_parts = [base_prompt, style_guide]

        # Add custom user preferences if provided
        if self.custom_prompt:
            custom_section = textwrap.dedent(f"""\

                Additional User Preferences:
                {self.custom_prompt}
            """)
            prompt_parts.append(custom_section)

            # Add reinforcement to prevent drift from core task
            reinforcement = textwrap.dedent("""\

                Remember: Your primary task is to create accurate, factual summaries of the article content.
                The user preferences above should guide your style and focus, but never override the core
                requirement to summarize the article truthfully and clearly.
            """)
            prompt_parts.append(reinforcement)

        return "\n".join(prompt_parts)

    async def summarize(self, article: Article) -> Article:
        """
        Generate a summary for an article using AI.

        Args:
            article: Article to summarize

        Returns:
            Article with summary field populated (original article if error occurs)
        """
        await self.prepare()

        # Handle minimal content - use excerpt instead of AI summarization
        if not article.content or len(article.content.strip()) < 100:
            logger.debug(f"Article '{article.title[:50]}...' has insufficient content for AI summarization")
            # Use first 150 characters as fallback summary
            article.summary = article.content[:150] + "..." if article.content else article.title
            return article

        # Prepare summarization prompt
        prompt = self._build_summarization_prompt(article)

        try:
            # Run AI summarization
            result = await self.agent.run(prompt)
            summary_result = result.output

            # Format summary based on style
            if self.summary_style == "bullet_points":
                # Format as bullet points
                formatted_summary = "\n".join(f"• {point}" for point in summary_result.key_points)
                article.summary = f"{summary_result.summary}\n\n{formatted_summary}"
            else:
                # Brief or detailed style
                article.summary = summary_result.summary

            # Log summary generation with custom prompt indicator
            custom_indicator = " with custom prompt" if self.custom_prompt else ""
            logger.debug(
                f"Generated {self.summary_style} summary{custom_indicator} for '{article.title[:50]}...': "
                f"{len(article.summary)} chars - {summary_result.reasoning}"
            )

            return article

        except Exception as e:
            logger.error(f"Error generating summary for article '{article.title[:50]}...': {e}")
            # On error, use excerpt from content as fallback
            article.summary = article.content[:300] + "..." if len(article.content) > 300 else article.content
            return article

    def _build_summarization_prompt(self, article: Article) -> str:
        """Build prompt for AI summarization."""
        # Truncate content to avoid token limits
        # Use configurable content length for summarization
        content = article.content[: self.settings.summary_content_length] if article.content else ""

        # Include tags for additional context
        tags_str = ", ".join(article.tags) if article.tags else "None"

        # Include topics if available (from TopicExtractor)
        topics_str = ", ".join(article.ai_topics) if article.ai_topics else "Not extracted"

        return textwrap.dedent(f"""\
            Article Title: {article.title}
            Tags: {tags_str}
            Topics: {topics_str}
            Content: {content}

            Create a {self.summary_style} summary of this article, focusing on the key information
            and main ideas that readers need to know.
        """)
