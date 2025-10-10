from datetime import datetime, time

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from app.models.base import ActiveLifecycleTimestampMixin, ULIDMixedIn


class User(SQLModel, ULIDMixedIn, ActiveLifecycleTimestampMixin, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_verified: bool = Field(default=False)
    timezone: str = Field(default="UTC")
    is_active: bool = Field(default=True)

    digest_config: "DigestConfiguration | None" = Relationship(back_populates="user")
    delivery_logs: list["DeliveryLog"] = Relationship(back_populates="user")


class DigestConfiguration(SQLModel, ULIDMixedIn, ActiveLifecycleTimestampMixin, table=True):
    __tablename__ = "digest_configurations"

    user_id: str = Field(foreign_key="users.id", index=True)
    delivery_time: time
    summary_style: str = Field(default="brief")
    is_active: bool = Field(default=True)

    user: User | None = Relationship(back_populates="digest_config")
    sources: list["ContentSource"] = Relationship(back_populates="config")
    interest_profile: "InterestProfile | None" = Relationship(back_populates="config")


class ContentSource(SQLModel, ULIDMixedIn, ActiveLifecycleTimestampMixin, table=True):
    __tablename__ = "content_sources"

    config_id: str = Field(foreign_key="digest_configurations.id", index=True)
    source_type: str
    source_url: str
    source_name: str
    is_active: bool = Field(default=True)

    # Validation fields
    validation_status: str = Field(default="pending")  # pending, valid, invalid, error
    last_validated_at: datetime | None = Field(default=None)
    validation_error: str | None = Field(default=None)
    last_fetch_at: datetime | None = Field(default=None)
    last_fetch_count: int = Field(default=0)

    config: DigestConfiguration | None = Relationship(back_populates="sources")


class InterestProfile(SQLModel, ULIDMixedIn, ActiveLifecycleTimestampMixin, table=True):
    __tablename__ = "interest_profiles"

    config_id: str = Field(foreign_key="digest_configurations.id", index=True)
    keywords: list[str] = Field(sa_column=Column(JSON), default=[])
    relevance_threshold: int = Field(default=40, ge=0, le=100)
    boost_factor: float = Field(default=1.0, ge=0.5, le=2.0)

    config: DigestConfiguration | None = Relationship(back_populates="interest_profile")


class DeliveryLog(SQLModel, ULIDMixedIn, ActiveLifecycleTimestampMixin, table=True):
    __tablename__ = "delivery_logs"

    user_id: str = Field(foreign_key="users.id", index=True)
    status: str
    article_count: str | None = None
    error_message: str | None = None

    user: User | None = Relationship(back_populates="delivery_logs")
