"""Digest configuration-related DTOs."""

from datetime import time

from pydantic import Field, HttpUrl

from app.dtos.base import FrozenBase


class UpdateDigestSettingsRequest(FrozenBase):
    """Input DTO for updating digest configuration settings."""

    delivery_time: time
    summary_style: str
    is_active: bool


class DigestSettingsResponse(FrozenBase):
    """
    Output DTO for digest configuration.

    Represents core digest settings without internal database details.
    """

    delivery_time: time
    summary_style: str
    is_active: bool


class CreateContentSourceRequest(FrozenBase):
    """Input DTO for creating a new content source."""

    source_type: str
    source_url: HttpUrl
    source_name: str = Field(min_length=1)


class ContentSourceResponse(FrozenBase):
    """
    Output DTO for content source.

    Includes ID for client-side reference and removal operations.
    """

    id: str
    source_type: str
    source_url: str
    source_name: str
    is_active: bool


class InterestProfileResponse(FrozenBase):
    """
    Output DTO for interest profile.

    Exposes keywords as list for API consumption.
    """

    keywords: list[str]
    relevance_threshold: int = Field(ge=0, le=100)
    boost_factor: float = Field(ge=0.5, le=2.0)


class UpdateInterestKeywordsRequest(FrozenBase):
    """Input DTO for updating interest profile keywords."""

    keywords: list[str]


class CompleteDigestConfigResponse(FrozenBase):
    """
    Composite output DTO containing full digest configuration.

    Combines config, sources, and interest profile for single API response.
    """

    config: DigestSettingsResponse
    sources: list[ContentSourceResponse]
    interest_profile: InterestProfileResponse


class InterestProfileUpdateRequest(FrozenBase):
    """Input DTO for updating interest profile keywords (comma-separated string)."""

    keywords: str


class DigestConfigResponse(FrozenBase):
    """Output DTO for digest configuration (flattened structure)."""

    delivery_time: str
    summary_style: str
    is_active: bool
    sources: list[ContentSourceResponse]
    interest_profile: dict
