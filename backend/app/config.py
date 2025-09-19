from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
