"""Digest-related DTOs."""

from datetime import datetime

from app.dtos.base import FrozenBase


class ArticleResponse(FrozenBase):
    """DTO for a single article in a digest."""

    title: str
    summary: str
    source_name: str
    url: str
    published_at: datetime


class DigestPreviewResponse(FrozenBase):
    """DTO for digest preview data."""

    articles: list[ArticleResponse]
    total_count: int
    generated_at: datetime


class DeliveryLogEntryResponse(FrozenBase):
    """DTO for a delivery log entry."""

    id: str
    status: str
    article_count: int | None
    error_message: str | None
    created_at: datetime
