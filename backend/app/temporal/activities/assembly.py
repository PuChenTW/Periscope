"""Digest assembly activities for Temporal workflows.

This module contains activities for assembling final digest payloads from
processed and grouped articles, with filtering, sorting, and HTML rendering.
"""

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Template as JinjaTemplate
from loguru import logger
from temporalio import activity

import app.temporal.activities.schemas as sc
from app.exceptions import NonRetryableError
from app.processors.relevance_scorer import RelevanceResult
from app.processors.similarity_detector import ArticleGroup


class DigestPayload(sc.BaseModel):
    """Final assembled digest ready for email delivery."""

    user_id: str
    user_email: str
    article_groups: list[ArticleGroup]
    html_body: str
    text_body: str
    generation_timestamp: datetime
    metadata: dict


class AssemblyActivities:
    """Activity class for digest assembly operations."""

    _TEMPLATE_DIR = Path(__file__).parent / "templates"
    _html_template: str | None = None
    _text_template: str | None = None

    def __init__(self):
        """Initialize assembly activities and load templates once."""
        # Load templates on first initialization (module-level caching)
        if AssemblyActivities._html_template is None:
            template_path = self._TEMPLATE_DIR / "digest.html"
            AssemblyActivities._html_template = template_path.read_text(encoding="utf-8")
        if AssemblyActivities._text_template is None:
            template_path = self._TEMPLATE_DIR / "digest.txt"
            AssemblyActivities._text_template = template_path.read_text(encoding="utf-8")

    @classmethod
    def _get_html_template(cls) -> str:
        """Get the cached HTML email template."""
        if cls._html_template is None:
            template_path = cls._TEMPLATE_DIR / "digest.html"
            cls._html_template = template_path.read_text(encoding="utf-8")
        return cls._html_template

    @classmethod
    def _get_text_template(cls) -> str:
        """Get the cached plain text email template."""
        if cls._text_template is None:
            template_path = cls._TEMPLATE_DIR / "digest.txt"
            cls._text_template = template_path.read_text(encoding="utf-8")
        return cls._text_template

    @activity.defn(name="assemble_digest")
    async def assemble_digest(
        self,
        user_id: str,
        user_email: str,
        article_groups: list[ArticleGroup],
        relevance_results: dict[str, RelevanceResult],
    ) -> DigestPayload:
        """
        Assemble final digest from grouped articles with filtering and HTML rendering.

        This activity:
        1. Filters articles by relevance threshold
        2. Sorts groups by relevance score
        3. Renders HTML and plain text versions
        4. Returns DigestPayload ready for email delivery

        Args:
            user_id: User ULID
            user_email: User email address
            article_groups: Grouped and summarized articles from similarity detector
            relevance_results: Relevance scoring results dict

        Returns:
            DigestPayload with rendered HTML/text bodies and metadata

        Raises:
            NonRetryableError: If template rendering fails (abort workflow)
        """
        start_timestamp = datetime.now(UTC)
        logger.info(f"Assembling digest for user {user_id} ({len(article_groups)} groups)")

        try:
            # Filter article groups by relevance threshold
            # Extract max relevance score per group (primary article)
            filtered_groups = []
            for group in article_groups:
                primary_url = str(group.primary_article.url)
                relevance_result = relevance_results.get(primary_url)

                if relevance_result is not None:
                    if relevance_result.passes_threshold:
                        filtered_groups.append((group, relevance_result.relevance_score))
                else:
                    # No relevance result: include by default with score 0
                    filtered_groups.append((group, 0))

            # Sort by relevance score (highest first)
            filtered_groups.sort(key=lambda x: x[1], reverse=True)
            sorted_groups = [g for g, _ in filtered_groups]

            logger.info(f"Filtered {len(sorted_groups)} groups from {len(article_groups)} (passed threshold)")

            # Render HTML template
            html_template = JinjaTemplate(self._get_html_template())
            html_body = html_template.render(
                article_groups=sorted_groups,
                date=datetime.now(UTC).strftime("%A, %B %d, %Y"),
                generated_at=datetime.now(UTC),
            )

            # Render text template
            text_template = JinjaTemplate(self._get_text_template())
            text_body = text_template.render(
                article_groups=sorted_groups,
                date=datetime.now(UTC).strftime("%A, %B %d, %Y"),
                generated_at=datetime.now(UTC),
            )

            end_timestamp = datetime.now(UTC)

            # Build metadata
            metadata = {
                "total_groups": len(sorted_groups),
                "total_articles": sum(1 + len(g.similar_articles) for g in sorted_groups),
                "html_size_bytes": len(html_body.encode()),
                "text_size_bytes": len(text_body.encode()),
                "assembly_time_ms": int((end_timestamp - start_timestamp).total_seconds() * 1000),
            }

            payload = DigestPayload(
                user_id=user_id,
                user_email=user_email,
                article_groups=sorted_groups,
                html_body=html_body,
                text_body=text_body,
                generation_timestamp=end_timestamp,
                metadata=metadata,
            )

            logger.info(f"Assembled digest: {metadata['total_articles']} articles in {metadata['total_groups']} groups")

            return payload

        except Exception as e:
            error_msg = f"Template rendering failed: {e}"
            logger.error(error_msg)
            raise NonRetryableError(error_msg) from e
