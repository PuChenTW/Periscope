from sqlalchemy import Boolean, Column, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    timezone = Column(String, nullable=False, default="UTC")
    is_active = Column(Boolean, default=True)

    digest_config = relationship(
        "DigestConfiguration", back_populates="user", uselist=False
    )
    delivery_logs = relationship("DeliveryLog", back_populates="user")


class DigestConfiguration(BaseModel):
    __tablename__ = "digest_configurations"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    delivery_time = Column(Time, nullable=False)
    summary_style = Column(String, nullable=False, default="brief")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="digest_config")
    sources = relationship("ContentSource", back_populates="config")
    interest_profile = relationship(
        "InterestProfile", back_populates="config", uselist=False
    )


class ContentSource(BaseModel):
    __tablename__ = "content_sources"

    config_id = Column(
        UUID(as_uuid=True),
        ForeignKey("digest_configurations.id"),
        nullable=False,
        index=True,
    )
    source_type = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    config = relationship("DigestConfiguration", back_populates="sources")


class InterestProfile(BaseModel):
    __tablename__ = "interest_profiles"

    config_id = Column(
        UUID(as_uuid=True),
        ForeignKey("digest_configurations.id"),
        nullable=False,
        index=True,
    )
    keywords = Column(String, nullable=False)

    config = relationship("DigestConfiguration", back_populates="interest_profile")


class DeliveryLog(BaseModel):
    __tablename__ = "delivery_logs"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    status = Column(String, nullable=False)
    article_count = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    user = relationship("User", back_populates="delivery_logs")
