"""
Content normalization service for standardizing article structure and metadata.

This module provides metadata enrichment and standardization for articles,
assuming articles have already been validated upstream.
"""

from datetime import UTC
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from loguru import logger
from pydantic import HttpUrl

from app.config import ContentNormalizationSettings, get_settings
from app.processors.fetchers.base import Article


class ContentNormalizer:
    """
    Normalizes article metadata for consistent processing.

    Assumes articles are already validated upstream. Handles date normalization,
    metadata standardization (title, author, tags, URL), and content length enforcement.
    Never raises exceptions - uses fallbacks and logs warnings instead.
    """

    def __init__(self, settings: ContentNormalizationSettings | None = None):
        """
        Initialize normalizer with configuration.

        Args:
            settings: Content normalization settings (uses get_settings().content if not provided)
        """
        self.settings = settings or get_settings().content

        # Extract individual fields for convenience
        self.content_max_length = self.settings.max_length
        self.title_max_length = self.settings.title_max_length
        self.author_max_length = self.settings.author_max_length
        self.tag_max_length = self.settings.tag_max_length
        self.max_tags_per_article = self.settings.max_tags_per_article

    def normalize(self, article: Article) -> Article:
        """
        Normalize an article's metadata.

        Assumes article is already validated upstream.

        Args:
            article: Validated article from upstream

        Returns:
            Normalized article with standardized metadata
        """
        # Phase 1: Date normalization - ensure UTC-aware published_at
        article = self._normalize_date(article)

        # Phase 2: Metadata standardization
        article = self._normalize_title(article)
        article = self._normalize_author(article)
        article = self._normalize_tags(article)
        article = self._normalize_url(article)
        article = self._enforce_content_length(article)

        return article

    def _normalize_date(self, article: Article) -> Article:
        """
        Normalize article published date to ensure UTC-aware timezone.

        Handles:
        - Naive datetime → Convert to UTC-aware
        - Non-UTC timezone → Convert to UTC
        - UTC timezone → Preserve unchanged

        Args:
            article: Article to normalize

        Returns:
            New Article with normalized UTC-aware published_at
        """
        # published_at should never be None (handled by fetcher)
        if article.published_at is None:
            # This shouldn't happen, but if it does, log warning and use fetch_timestamp
            logger.warning(f"Article '{article.title[:50]}...' has None published_at, using fetch_timestamp")
            return article.model_copy(update={"published_at": article.fetch_timestamp})

        # Handle naive datetime (no timezone info)
        if article.published_at.tzinfo is None:
            # Assume naive datetime is UTC and mark it as such
            logger.debug(f"Article '{article.title[:50]}...' has naive datetime, converting to UTC-aware")
            return article.model_copy(update={"published_at": article.published_at.replace(tzinfo=UTC)})

        # Handle aware datetime that's not in UTC
        if article.published_at.tzinfo != UTC:
            # Convert to UTC
            logger.debug(f"Article '{article.title[:50]}...' converted from {article.published_at.tzinfo} to UTC")
            return article.model_copy(update={"published_at": article.published_at.astimezone(UTC)})

        return article

    def _normalize_title(self, article: Article) -> Article:
        """
        Normalize article title: cleanup whitespace, enforce max length, fallback.

        Args:
            article: Article to normalize

        Returns:
            New Article with normalized title
        """
        if not article.title or not article.title.strip():
            logger.debug("Article has empty title, using fallback")
            return article.model_copy(update={"title": "Untitled Article"})

        # Clean up whitespace
        title = " ".join(article.title.split())

        # Enforce max length with smart truncation
        if len(title) > self.title_max_length:
            title = title[: self.title_max_length].rsplit(" ", 1)[0] + "..."
            logger.debug(f"Title truncated to {self.title_max_length} chars")

        return article.model_copy(update={"title": title})

    def _normalize_author(self, article: Article) -> Article:
        """
        Normalize author name: title case, cleanup whitespace, enforce max length.

        Args:
            article: Article to normalize

        Returns:
            New Article with normalized author
        """
        if not article.author or not article.author.strip():
            return article

        # Clean up whitespace and apply title case
        author = " ".join(article.author.split())
        author = author.title()

        # Enforce max length with truncation
        if len(author) > self.author_max_length:
            author = author[: self.author_max_length].rsplit(" ", 1)[0] + "..."
            logger.debug(f"Author name truncated to {self.author_max_length} chars")

        return article.model_copy(update={"author": author})

    def _normalize_tags(self, article: Article) -> Article:
        """
        Normalize tags: lowercase, deduplicate, enforce limits.

        Args:
            article: Article to normalize

        Returns:
            New Article with normalized tags
        """
        if not article.tags:
            return article

        # Normalize and deduplicate tags
        normalized_tags = []
        seen = set()

        for t in article.tags:
            # Clean up and lowercase
            tag = t.strip().lower()

            # Skip empty tags
            if not tag:
                continue

            tag = tag[: self.tag_max_length]

            # Deduplicate
            if tag not in seen:
                normalized_tags.append(tag)
                seen.add(tag)

            # Stop at max tags
            if len(normalized_tags) >= self.max_tags_per_article:
                break

        return article.model_copy(update={"tags": normalized_tags})

    def _normalize_url(self, article: Article) -> Article:
        """
        Normalize article URL for canonical form and cache key consistency.

        Transformations:
        1. Remove tracking parameters (utm_*, fbclid, gclid, ref, source, campaign)
        2. Sort query parameters alphabetically
        3. Strip URL fragments (#anchor)
        4. Normalize domain to lowercase
        5. Upgrade HTTP to HTTPS

        Args:
            article: Article to normalize

        Returns:
            New Article with normalized URL
        """
        url_str = str(article.url)
        parsed = urlparse(url_str)

        # 1. Remove tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "fbclid",
            "gclid",
            "ref",
            "source",
            "campaign",
        }

        # 2. Filter and sort query parameters
        query_params = parse_qs(parsed.query, keep_blank_values=True) if parsed.query else {}
        filtered_params = {k: v for k, v in query_params.items() if k not in tracking_params}
        sorted_query = urlencode(sorted(filtered_params.items()), doseq=True) if filtered_params else ""

        # 3. Upgrade to HTTPS
        scheme = "https" if parsed.scheme == "http" else parsed.scheme

        # 4. Normalize domain to lowercase
        netloc = parsed.netloc.lower()

        # 5. Rebuild URL without fragment (stripped)
        normalized_url = urlunparse((scheme, netloc, parsed.path, parsed.params, sorted_query, ""))

        return article.model_copy(update={"url": HttpUrl(normalized_url)})

    def _enforce_content_length(self, article: Article) -> Article:
        """
        Enforce maximum content length with smart truncation.

        Args:
            article: Article to normalize

        Returns:
            New Article with content truncated if needed
        """
        if not article.content or len(article.content) <= self.content_max_length:
            return article

        # Capture original length before truncation
        original_length = len(article.content)

        # Truncate at word boundary
        truncated = article.content[: self.content_max_length]
        truncated = truncated.rsplit(" ", 1)[0]

        logger.debug(f"Content truncated from {original_length} to {len(truncated)} chars")

        return article.model_copy(update={"content": truncated})
