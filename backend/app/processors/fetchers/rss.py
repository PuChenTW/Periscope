import html
import re
from contextlib import suppress
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
from loguru import logger
from pydantic import HttpUrl

from app.processors.fetchers.base import Article, BaseFetcher, FetchResult, SourceInfo, SourceType
from app.processors.fetchers.exceptions import FetchTimeoutError
from app.processors.utils.http_client import HTTPClient
from app.processors.utils.url_validation import is_valid_url, validate_rss_feed


class RSSFetcher(BaseFetcher):
    """RSS feed content fetcher using feedparser."""

    @property
    def source_type(self) -> str:
        return SourceType.RSS

    async def validate_url(self, url: str) -> bool:
        """Validate if URL is a valid RSS feed."""
        try:
            await validate_rss_feed(url)
            return True
        except Exception:
            return False

    async def fetch_content(self, url: str) -> FetchResult:
        """Fetch and parse RSS feed content."""
        if not is_valid_url(url):
            try:
                source_url = HttpUrl(url)
            except Exception:
                source_url = HttpUrl("https://invalid-url.placeholder")

            return FetchResult(
                source_info=SourceInfo(title="Invalid URL", url=source_url),
                articles=[],
                fetch_timestamp=datetime.now(),
                success=False,
                error_message="Invalid URL format",
            )

        try:
            async with HTTPClient(timeout=self.timeout) as client:
                content = await client.fetch_text(url)

            feed = feedparser.parse(content)

            if not feed.entries:
                return FetchResult(
                    source_info=await self.get_source_info(url),
                    articles=[],
                    fetch_timestamp=datetime.now(),
                    success=False,
                    error_message="No articles found in feed",
                )

            source_info = await self._extract_source_info(feed, url)
            articles = await self._extract_articles(feed.entries[: self.max_articles])

            return FetchResult(source_info=source_info, articles=articles, fetch_timestamp=datetime.now(), success=True)

        except FetchTimeoutError:
            logger.warning(f"Timeout fetching RSS feed: {url}")
            return FetchResult(
                source_info=SourceInfo(title="Timeout", url=HttpUrl(url)),
                articles=[],
                fetch_timestamp=datetime.now(),
                success=False,
                error_message="Request timeout",
            )
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return FetchResult(
                source_info=SourceInfo(title="Error", url=HttpUrl(url)),
                articles=[],
                fetch_timestamp=datetime.now(),
                success=False,
                error_message=str(e),
            )

    async def get_source_info(self, url: str) -> SourceInfo:
        """Get RSS feed metadata."""
        try:
            async with HTTPClient(timeout=self.timeout) as client:
                content = await client.fetch_text(url)

            feed = feedparser.parse(content)
            return await self._extract_source_info(feed, url)

        except Exception as e:
            logger.error(f"Error getting source info for {url}: {e}")
            return SourceInfo(title="Unknown Feed", url=HttpUrl(url), description="Unable to fetch source information")

    async def _extract_source_info(self, feed, url: str) -> SourceInfo:
        """Extract source metadata from feedparser feed object."""
        feed_info = feed.feed

        last_updated = None
        if hasattr(feed_info, "updated"):
            with suppress(Exception):
                last_updated = parsedate_to_datetime(feed_info.updated)

        return SourceInfo(
            title=feed_info.get("title", "Unknown Feed"),
            description=self._clean_text(feed_info.get("description", "")),
            url=HttpUrl(url),
            language=feed_info.get("language"),
            last_updated=last_updated,
            metadata={
                "version": getattr(feed, "version", None),
                "generator": feed_info.get("generator"),
                "link": feed_info.get("link"),
                "subtitle": feed_info.get("subtitle"),
            },
        )

    async def _extract_articles(self, entries: list) -> list[Article]:
        """Extract articles from RSS feed entries."""
        articles = []

        for entry in entries:
            try:
                article = await self._parse_entry(entry)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing RSS entry: {e}")
                continue

        return articles

    async def _parse_entry(self, entry) -> Article | None:
        """Parse individual RSS entry into Article."""
        try:
            # Extract title
            title = entry.get("title", "Untitled").strip()
            if not title:
                return None

            # Extract URL
            link = entry.get("link")
            if not link or not is_valid_url(link):
                return None

            # Extract content (prefer content over summary over description)
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else entry.content
            elif entry.get("summary"):
                content = entry.summary
            elif entry.get("description"):
                content = entry.description

            content = self._clean_text(content)

            # Extract published date
            published_at = None
            if entry.get("published"):
                with suppress(Exception):
                    published_at = parsedate_to_datetime(entry.published)

            # Extract author
            author = None
            if entry.get("author"):
                author = entry.author
            elif entry.get("author_detail", {}).get("name"):
                author = entry.author_detail.name

            # Extract tags/categories
            tags = []
            if hasattr(entry, "tags") and entry.tags:
                tags = [tag.term for tag in entry.tags if hasattr(tag, "term")]

            return Article(
                title=title,
                url=HttpUrl(link),
                content=content,
                published_at=published_at,
                author=author,
                tags=tags,
                metadata={
                    "guid": entry.get("id", entry.get("guid")),
                    "comments": entry.get("comments"),
                    "source": entry.get("source", {}).get("href") if entry.get("source") else None,
                },
            )

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean HTML tags and normalize whitespace from text."""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = html.unescape(text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text
