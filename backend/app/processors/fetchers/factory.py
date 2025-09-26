from urllib.parse import urlparse

from app.processors.fetchers.base import BaseFetcher, SourceType
from app.processors.fetchers.exceptions import InvalidUrlError
from app.processors.fetchers.rss import RSSFetcher


class FetcherRegistry:
    """Registry for content fetchers."""

    def __init__(self):
        self._fetchers: dict[SourceType, type[BaseFetcher]] = {}

    def register(self, source_type: SourceType, fetcher_class: type[BaseFetcher]):
        """Register a fetcher for a specific source type."""
        self._fetchers[source_type] = fetcher_class

    def get_fetcher(self, source_type: SourceType) -> type[BaseFetcher]:
        """Get fetcher class for source type."""
        if source_type not in self._fetchers:
            raise ValueError(f"No fetcher registered for source type: {source_type}")
        return self._fetchers[source_type]

    def list_supported_types(self) -> list[SourceType]:
        """Get list of supported source types."""
        return list(self._fetchers.keys())


# Global registry instance
registry = FetcherRegistry()

# Register default fetchers
registry.register(SourceType.RSS, RSSFetcher)


def create_fetcher(source_type: SourceType, **kwargs) -> BaseFetcher:
    """Create a fetcher instance for the given source type."""
    fetcher_class = registry.get_fetcher(source_type)
    return fetcher_class(**kwargs)


async def detect_source_type(url: str) -> SourceType:
    """Detect the source type from URL."""
    if not url:
        raise InvalidUrlError("Empty URL provided")

    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        raise InvalidUrlError(f"Invalid URL format: {url}")

    # Only allow HTTP/HTTPS schemes for content fetching
    if parsed.scheme.lower() not in ["http", "https"]:
        raise InvalidUrlError(f"Unsupported URL scheme: {parsed.scheme}")

    # For now, assume all URLs are RSS feeds
    # In the future, this could include logic to:
    # - Check content-type headers
    # - Look for RSS autodiscovery
    # - Detect blog platforms
    # - Try different fetcher types

    # Check for common RSS patterns in URL
    path = parsed.path.lower()
    rss_indicators = ["rss", "feed", "atom", ".xml", "/feeds/", "/feed/", "/rss/"]

    if any(indicator in path for indicator in rss_indicators):
        return SourceType.RSS

    # Default to RSS for now - will enhance with proper detection later
    return SourceType.RSS


async def auto_create_fetcher(url: str, **kwargs) -> BaseFetcher:
    """Automatically detect source type and create appropriate fetcher."""
    source_type = await detect_source_type(url)
    return create_fetcher(source_type, **kwargs)
