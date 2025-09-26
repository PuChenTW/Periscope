from functools import cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Personal Daily Reading Digest"
    debug: bool = Field(False, env="DEBUG")

    database_url: str = Field(..., env="DATABASE_URL")

    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_expire_minutes: int = Field(30, env="JWT_EXPIRE_MINUTES")

    email_provider: str = Field("smtp", env="EMAIL_PROVIDER")
    email_api_key: str = Field("", env="EMAIL_API_KEY")
    smtp_host: str = Field("localhost", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str = Field("", env="SMTP_USERNAME")
    smtp_password: str = Field("", env="SMTP_PASSWORD")

    cache_ttl_minutes: int = Field(60, env="CACHE_TTL_MINUTES")

    # RSS Fetcher Settings
    rss_fetch_timeout: int = Field(30, env="RSS_FETCH_TIMEOUT")
    rss_max_retries: int = Field(3, env="RSS_MAX_RETRIES")
    rss_retry_delay: float = Field(1.0, env="RSS_RETRY_DELAY")
    rss_max_articles_per_feed: int = Field(100, env="RSS_MAX_ARTICLES_PER_FEED")
    rss_user_agent: str = Field("Periscope-Bot/1.0 (+https://periscope.ai/bot)", env="RSS_USER_AGENT")


@cache
def get_settings() -> Settings:
    return Settings()
