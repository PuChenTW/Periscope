from datetime import time
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_verified: bool = Field(default=False)
    timezone: str = Field(default="UTC")
    is_active: bool = Field(default=True)

    digest_config: "DigestConfiguration | None" = Relationship(back_populates="user")
    delivery_logs: list["DeliveryLog"] = Relationship(back_populates="user")


class DigestConfiguration(BaseModel, table=True):
    __tablename__ = "digest_configurations"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    delivery_time: time
    summary_style: str = Field(default="brief")
    is_active: bool = Field(default=True)

    user: User | None = Relationship(back_populates="digest_config")
    sources: list["ContentSource"] = Relationship(back_populates="config")
    interest_profile: "InterestProfile | None" = Relationship(
        back_populates="config"
    )


class ContentSource(BaseModel, table=True):
    __tablename__ = "content_sources"

    config_id: UUID = Field(foreign_key="digest_configurations.id", index=True)
    source_type: str
    source_url: str
    source_name: str
    is_active: bool = Field(default=True)

    config: DigestConfiguration | None = Relationship(back_populates="sources")


class InterestProfile(BaseModel, table=True):
    __tablename__ = "interest_profiles"

    config_id: UUID = Field(foreign_key="digest_configurations.id", index=True)
    keywords: str

    config: DigestConfiguration | None = Relationship(
        back_populates="interest_profile"
    )


class DeliveryLog(BaseModel, table=True):
    __tablename__ = "delivery_logs"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    status: str
    article_count: str | None = None
    error_message: str | None = None

    user: User | None = Relationship(back_populates="delivery_logs")
