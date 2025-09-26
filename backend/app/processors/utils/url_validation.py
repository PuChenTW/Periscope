import re
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from app.processors.fetchers.exceptions import InvalidUrlError, ValidationError
from app.processors.utils.http_client import HTTPClient


def is_valid_url(url: str) -> bool:
    """Check if URL has valid format."""
    try:
        result = urlparse(url)
        return all([result.scheme.strip(), result.netloc.strip()])
    except Exception:
        return False


async def discover_rss_feeds(url: str) -> list[str]:
    """Discover RSS feeds from a website URL."""
    if not is_valid_url(url):
        raise InvalidUrlError(f"Invalid URL: {url}")

    feeds = []

    async with HTTPClient() as client:
        try:
            html_content = await client.fetch_text(url)
            soup = BeautifulSoup(html_content, "html.parser")

            # Look for RSS/Atom link elements
            link_elements = soup.find_all("link", {"type": re.compile(r"application/(rss|atom)\+xml")})
            for link in link_elements:
                feed_url = link.get("href")
                if feed_url:
                    # Convert relative URLs to absolute
                    feed_url = urljoin(url, feed_url)
                    feeds.append(feed_url)

            # Common RSS feed paths to try
            common_paths = [
                "/rss.xml",
                "/feed.xml",
                "/atom.xml",
                "/feed/",
                "/feeds/",
                "/rss/",
                "/blog/feed/",
                "/news/feed/",
                "/feed.rss",
            ]

            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            for path in common_paths:
                potential_feed = urljoin(base_url, path)
                if potential_feed not in feeds and await _is_valid_rss_feed(potential_feed, client):
                    feeds.append(potential_feed)

        except Exception as e:
            logger.warning(f"Error discovering feeds for {url}: {e}")

    return feeds


async def _is_valid_rss_feed(url: str, client: HTTPClient) -> bool:
    """Check if URL returns valid RSS feed."""
    try:
        content = await client.fetch_text(url)
        feed = feedparser.parse(content)
        return bool(feed.entries and hasattr(feed, "version"))
    except Exception:
        return False


async def validate_rss_feed(url: str) -> dict:
    """Validate RSS feed and return metadata."""
    if not is_valid_url(url):
        raise InvalidUrlError(f"Invalid URL: {url}")

    async with HTTPClient() as client:
        try:
            content = await client.fetch_text(url)
            feed = feedparser.parse(content)

            if not feed.entries:
                raise ValidationError(f"No entries found in feed: {url}")

            if not hasattr(feed, "version"):
                raise ValidationError(f"Not a valid RSS/Atom feed: {url}")

            return {
                "title": feed.feed.get("title", "Unknown"),
                "description": feed.feed.get("description", ""),
                "link": feed.feed.get("link", url),
                "version": feed.version,
                "language": feed.feed.get("language"),
                "entries_count": len(feed.entries),
                "last_updated": getattr(feed.feed, "updated", None),
            }

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to validate RSS feed {url}: {e}") from e


async def check_url_health(url: str) -> bool:
    """Simple health check for URL accessibility."""
    try:
        async with HTTPClient(timeout=10) as client:
            await client.fetch_text(url)
            return True
    except Exception as e:
        logger.warning(f"Health check failed for {url}: {e}")
        return False
