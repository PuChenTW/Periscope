from functools import cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration."""

    url: str


class RedisSettings(BaseModel):
    """Redis cache configuration."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 10


class CacheSettings(BaseModel):
    """General cache configuration."""

    ttl_minutes: int = 60


class EmailSettings(BaseModel):
    """Email provider configuration."""

    provider: str = "smtp"
    api_key: str = ""
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""


class AISettings(BaseModel):
    """AI provider configuration."""

    provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    openai_api_key: str = ""
    openai_model: str = "gpt-5-nano"


class RSSSettings(BaseModel):
    """RSS fetcher configuration."""

    fetch_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_articles_per_feed: int = 100
    user_agent: str = "Periscope-Bot/1.0 (+https://periscope.ai/bot)"


class SimilaritySettings(BaseModel):
    """Similarity detection configuration."""

    threshold: float = 0.7
    cache_ttl_minutes: int = 1440
    batch_size: int = 10


class TopicExtractionSettings(BaseModel):
    """Topic extraction configuration."""

    max_topics: int = 5
    cache_ttl_minutes: int = 1440  # 24 hours


class SummarizationSettings(BaseModel):
    """Summarization configuration."""

    max_length: int = 500
    content_length: int = 2000
    cache_ttl_minutes: int = 720  # 12 hours


class CustomPromptSettings(BaseModel):
    """Custom prompt validation configuration."""

    max_length: int = 1000
    min_length: int = 10
    validation_enabled: bool = True


class AIPromptValidationSettings(BaseModel):
    """AI-powered prompt validation configuration (final guardrail layer)."""

    enabled: bool = True
    threshold: float = 0.8
    cache_ttl_minutes: int = 1440


class ContentNormalizationSettings(BaseModel):
    """Content normalization and quality configuration."""

    min_length: int = 100
    max_length: int = 50000
    spam_detection_enabled: bool = True
    spam_detection_cache_ttl_minutes: int = 1440  # 24 hours
    title_max_length: int = 500
    author_max_length: int = 100
    tag_max_length: int = 50
    max_tags_per_article: int = 20
    quality_scoring_enabled: bool = True
    quality_cache_ttl_minutes: int = 720  # 12 hours


class PersonalizationSettings(BaseModel):
    """Personalization and relevance scoring configuration."""

    keyword_weight_title: int = 3
    keyword_weight_content: int = 2
    keyword_weight_tags: int = 4
    max_keywords: int = 50
    relevance_threshold_default: int = 40
    boost_factor_default: float = 1.0
    cache_ttl_minutes: int = 720
    enable_semantic_scoring: bool = True


class SecuritySettings(BaseModel):
    """Security and authentication configuration."""

    secret_key: str
    jwt_expire_minutes: int = 30


class TemporalSettings(BaseModel):
    """Temporal workflow orchestration configuration."""

    server_url: str = "localhost:7233"
    namespace: str = "default"
    task_queue: str = "periscope-digest"
    client_identity: str = "periscope-client"


class Settings(BaseSettings):
    """Main application settings with nested configuration groups.

    Environment variables can be set using double underscore (__) as delimiter:
    - DATABASE__URL for database.url
    - AI__GEMINI_API_KEY for ai.gemini_api_key
    - SIMILARITY__THRESHOLD for similarity.threshold
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    app_name: str = "Personal Daily Reading Digest"
    debug: bool = False
    test_mode: bool = False

    # Nested configuration groups
    database: DatabaseSettings
    redis: RedisSettings = RedisSettings()
    cache: CacheSettings = CacheSettings()
    email: EmailSettings = EmailSettings()
    ai: AISettings = AISettings()
    rss: RSSSettings = RSSSettings()
    similarity: SimilaritySettings = SimilaritySettings()
    topic_extraction: TopicExtractionSettings = TopicExtractionSettings()
    summarization: SummarizationSettings = SummarizationSettings()
    custom_prompt: CustomPromptSettings = CustomPromptSettings()
    ai_validation: AIPromptValidationSettings = AIPromptValidationSettings()
    content: ContentNormalizationSettings = ContentNormalizationSettings()
    personalization: PersonalizationSettings = PersonalizationSettings()
    security: SecuritySettings
    temporal: TemporalSettings = TemporalSettings()


@cache
def get_settings() -> Settings:
    return Settings()
