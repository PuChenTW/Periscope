"""Schemas for batch processing activities."""

from datetime import datetime, time

from pydantic import BaseModel, Field

from app.processors.fetchers.base import Article
from app.processors.quality_scorer import ContentQualityResult
from app.processors.relevance_scorer import RelevanceResult
from app.processors.similarity_detector import ArticleGroup
from app.processors.summarizer import SummaryResult
from app.processors.validator import ValidationResult


class BaseActivityResult(BaseModel):
    """Base result model with standard timing observability."""

    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")


class AIActivityResult(BaseActivityResult):
    """Base result model for AI-powered activities with metrics tracking."""

    ai_calls: int = Field(default=0, description="Number of AI calls made")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class ContentSourceConfig(BaseModel):
    """Configuration for a single content source."""

    id: str = Field(description="Source ULID")
    source_type: str = Field(description="Type of source (rss, blog, etc.)")
    source_url: str = Field(description="URL of the source")
    source_name: str = Field(description="Human-readable source name")
    is_active: bool = Field(description="Whether this source is active")


class InterestProfileConfig(BaseModel):
    """User interest profile configuration."""

    id: str = Field(description="Profile ULID")
    keywords: list[str] = Field(description="Keywords for interest matching")
    relevance_threshold: int = Field(description="Relevance score threshold (0-100)")
    boost_factor: float = Field(description="Boost factor for matching articles")


class DigestUserConfig(BaseModel):
    """Complete user configuration for digest generation."""

    user_id: str = Field(description="User ULID")
    email: str = Field(description="User email address")
    timezone: str = Field(description="User timezone (e.g., 'UTC')")
    delivery_time: time = Field(description="Preferred delivery time")
    summary_style: str = Field(description="Summary style (brief, detailed, bullet_points)")
    is_active: bool = Field(description="Whether digest generation is active")
    sources: list[ContentSourceConfig] = Field(description="List of content sources")
    interest_profile: InterestProfileConfig = Field(description="Interest profile configuration")


class FetchUserConfigRequest(BaseModel):
    """Request to fetch user configuration for digest generation."""

    user_id: str = Field(description="User ULID to fetch config for")


class FetchUserConfigResult(BaseActivityResult):
    """Result of fetching user configuration."""

    user_config: DigestUserConfig = Field(description="Complete user configuration")
    sources_count: int = Field(description="Number of active sources")
    keywords_count: int = Field(description="Number of interest keywords")


class BatchValidationRequest(BaseModel):
    """Request for batch article validation and filtering."""

    articles: list[Article] = Field(description="Articles to validate")


class BatchValidationResult(AIActivityResult):
    """Result of batch article validation and filtering."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    validation_results: dict[str, ValidationResult] = Field(description="Validation results keyed by article.url")
    total_processed: int = Field(description="Total articles validated")
    valid_count: int = Field(description="Articles that passed all checks")
    invalid_count: int = Field(description="Articles rejected (empty/short/spam)")


class BatchNormalizationRequest(BaseModel):
    """Request for batch article normalization."""

    articles: list[Article] = Field(description="Articles to normalize")


class BatchNormalizationResult(AIActivityResult):
    """Result of batch article normalization."""

    articles: list[Article] = Field(description="Normalized articles (rejected articles filtered out)")
    total_processed: int = Field(description="Total articles processed")
    rejected_count: int = Field(description="Articles rejected (spam, too short, etc.)")
    spam_detected_count: int = Field(description="Articles rejected as spam")


class BatchQualityRequest(BaseModel):
    """Request for batch quality scoring."""

    articles: list[Article] = Field(description="Articles to score")


class BatchQualityResult(AIActivityResult):
    """Result of batch quality scoring."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    quality_results: dict[str, ContentQualityResult] = Field(description="Quality results keyed by article.url")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")


class BatchTopicExtractionRequest(BaseModel):
    """Request for batch topic extraction."""

    articles: list[Article] = Field(description="Articles to extract topics from")


class BatchTopicExtractionResult(AIActivityResult):
    """Result of batch topic extraction."""

    articles: list[Article] = Field(description="Articles with ai_topics populated")
    total_processed: int = Field(description="Total articles processed")
    articles_with_topics: int = Field(description="Articles that got non-empty topics")
    cache_hits: int = Field(description="Number of results served from cache")


class BatchRelevanceRequest(BaseModel):
    """Request for batch relevance scoring."""

    profile_id: str = Field(description="Interest profile ID to score against")
    articles: list[Article] = Field(description="List of articles to score")
    quality_scores: dict[str, int] | None = Field(
        default=None,
        description="Optional quality scores keyed by article.url (from QualityScorer activity)",
    )


class BatchRelevanceResult(AIActivityResult):
    """Result of batch relevance scoring."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    relevance_results: dict[str, RelevanceResult] = Field(description="Relevance results keyed by article.url")
    profile_id: str = Field(description="Interest profile ID used for scoring")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")
    ai_calls: int = Field(default=0, description="Number of AI calls made (excluding cache hits)")
    errors_count: int = Field(default=0, description="Number of errors encountered (with fallbacks applied)")


class BatchSummarizationRequest(BaseModel):
    """Request for batch article summarization."""

    articles: list[Article] = Field(description="Articles to summarize")
    summary_style: str = Field(
        default="brief",
        description="Summary style (brief, detailed, bullet_points)",
    )
    custom_prompt: str | None = Field(
        default=None,
        description="Optional user-defined custom summarization prompt",
    )


class BatchSummarizationResult(AIActivityResult):
    """Result of batch article summarization."""

    articles: list[Article] = Field(description="Articles with summary field populated")
    summary_results: dict[str, SummaryResult] = Field(description="Summarization results keyed by article.url")
    total_summarized: int = Field(description="Total articles summarized")
    cache_hits: int = Field(description="Number of results served from cache")
    articles_with_summary: int = Field(description="Articles that got non-empty summaries")


class BatchSimilarityRequest(BaseModel):
    """Request for batch similarity detection."""

    articles: list[Article] = Field(description="Articles to detect similarity between")


class BatchSimilarityResult(AIActivityResult):
    """Result of batch similarity detection."""

    article_groups: list[ArticleGroup] = Field(description="Articles grouped by semantic similarity")
    total_articles: int = Field(description="Total articles processed")
    total_groups: int = Field(description="Number of article groups created")
    articles_grouped: int = Field(description="Articles included in groups (vs orphaned)")
    cache_hits: int = Field(default=0, description="Number of cached comparison results reused")
