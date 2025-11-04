"""Schemas for batch processing activities."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.processors.fetchers.base import Article
from app.processors.quality_scorer import ContentQualityResult
from app.processors.relevance_scorer import RelevanceResult
from app.processors.validator import ValidationResult


class BatchValidationRequest(BaseModel):
    """Request for batch article validation and filtering."""

    articles: list[Article] = Field(description="Articles to validate")


class BatchValidationResult(BaseModel):
    """Result of batch article validation and filtering."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    validation_results: dict[str, ValidationResult] = Field(description="Validation results keyed by article.url")
    total_processed: int = Field(description="Total articles validated")
    valid_count: int = Field(description="Articles that passed all checks")
    invalid_count: int = Field(description="Articles rejected (empty/short/spam)")

    # Standard observability
    ai_calls: int = Field(default=0, description="Number of AI calls made (spam detection only)")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchNormalizationRequest(BaseModel):
    """Request for batch article normalization."""

    articles: list[Article] = Field(description="Articles to normalize")


class BatchNormalizationResult(BaseModel):
    """Result of batch article normalization."""

    articles: list[Article] = Field(description="Normalized articles (rejected articles filtered out)")
    total_processed: int = Field(description="Total articles processed")
    rejected_count: int = Field(description="Articles rejected (spam, too short, etc.)")
    spam_detected_count: int = Field(description="Articles rejected as spam")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made (spam detection)")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchQualityRequest(BaseModel):
    """Request for batch quality scoring."""

    articles: list[Article] = Field(description="Articles to score")


class BatchQualityResult(BaseModel):
    """Result of batch quality scoring."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    quality_results: dict[str, ContentQualityResult] = Field(description="Quality results keyed by article.url")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchTopicExtractionRequest(BaseModel):
    """Request for batch topic extraction."""

    articles: list[Article] = Field(description="Articles to extract topics from")


class BatchTopicExtractionResult(BaseModel):
    """Result of batch topic extraction."""

    articles: list[Article] = Field(description="Articles with ai_topics populated")
    total_processed: int = Field(description="Total articles processed")
    articles_with_topics: int = Field(description="Articles that got non-empty topics")
    cache_hits: int = Field(description="Number of results served from cache")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchRelevanceRequest(BaseModel):
    """Request for batch relevance scoring."""

    profile_id: str = Field(description="Interest profile ID to score against")
    articles: list[Article] = Field(description="List of articles to score")
    quality_scores: dict[str, int] | None = Field(
        default=None,
        description="Optional quality scores keyed by article.url (from QualityScorer activity)",
    )


class BatchRelevanceResult(BaseModel):
    """Result of batch relevance scoring."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    relevance_results: dict[str, RelevanceResult] = Field(description="Relevance results keyed by article.url")
    profile_id: str = Field(description="Interest profile ID used for scoring")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made (excluding cache hits)")
    errors_count: int = Field(default=0, description="Number of errors encountered (with fallbacks applied)")
