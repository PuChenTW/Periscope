from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel, HttpUrl


class Article(BaseModel):
    title: str
    url: HttpUrl
    content: str
    summary: str | None = None
    published_at: datetime | None = None
    author: str | None = None
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class SourceInfo(BaseModel):
    title: str
    description: str | None = None
    url: HttpUrl
    language: str | None = None
    last_updated: datetime | None = None
    metadata: dict[str, Any] = {}


class FetchResult(BaseModel):
    source_info: SourceInfo
    articles: list[Article]
    fetch_timestamp: datetime
    success: bool = True
    error_message: str | None = None


class SourceType(StrEnum):
    RSS = auto()


class BaseFetcher(ABC):
    """Abstract base class for content fetchers."""

    def __init__(self, timeout: int = 30, max_articles: int = 100):
        self.timeout = timeout
        self.max_articles = max_articles

    @abstractmethod
    async def validate_url(self, url: str) -> bool:
        """Validate if the URL is accessible and contains the expected content type."""
        pass

    @abstractmethod
    async def fetch_content(self, url: str) -> FetchResult:
        """Fetch and parse content from the given URL."""
        pass

    @abstractmethod
    async def get_source_info(self, url: str) -> SourceInfo:
        """Get metadata information about the source."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the type of source this fetcher handles."""
        pass
