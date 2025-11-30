"""
Mapper functions for converting between Domain Models and DTOs.

All mappers are pure functions with no side effects.
Domain Models → DTOs: Extract and expose only what's needed
DTOs → Domain Models: Construct entities for persistence
"""

from app.dtos.auth import UserAuthDTO
from app.dtos.config import (
    CompleteDigestConfigDTO,
    ContentSourceDTO,
    DigestConfigDTO,
    InterestProfileDTO,
)
from app.dtos.user import UserDTO
from app.models.users import ContentSource, DigestConfiguration, InterestProfile, User


# User Mappers
def user_to_dto(user: User) -> UserDTO:
    """
    Convert User entity to UserDTO.

    Excludes: hashed_password, created_at, updated_at, relationships
    """
    return UserDTO(
        id=user.id,
        email=user.email,
        timezone=user.timezone,
        is_verified=user.is_verified,
        is_active=user.is_active,
    )


def user_to_auth_dto(user: User) -> UserAuthDTO:
    """
    Convert User entity to UserAuthDTO (used after registration/login).

    Same fields as UserDTO but semantically represents authenticated context.
    """
    return UserAuthDTO(
        id=user.id,
        email=user.email,
        timezone=user.timezone,
        is_verified=user.is_verified,
        is_active=user.is_active,
    )


# Digest Configuration Mappers
def digest_config_to_dto(config: DigestConfiguration) -> DigestConfigDTO:
    """
    Convert DigestConfiguration entity to DigestConfigDTO.

    Excludes: id, user_id, created_at, updated_at, relationships
    """
    return DigestConfigDTO(
        delivery_time=config.delivery_time,
        summary_style=config.summary_style,
        is_active=config.is_active,
    )


# Content Source Mappers
def content_source_to_dto(source: ContentSource) -> ContentSourceDTO:
    """
    Convert ContentSource entity to ContentSourceDTO.

    Includes: id (needed for deletion), core source fields
    Excludes: config_id, validation fields, timestamps, relationships
    """
    return ContentSourceDTO(
        id=source.id,
        source_type=source.source_type,
        source_url=source.source_url,
        source_name=source.source_name,
        is_active=source.is_active,
    )


def content_sources_to_dtos(sources: list[ContentSource]) -> list[ContentSourceDTO]:
    """Convert list of ContentSource entities to list of DTOs."""
    return [content_source_to_dto(source) for source in sources]


# Interest Profile Mappers
def interest_profile_to_dto(profile: InterestProfile) -> InterestProfileDTO:
    """
    Convert InterestProfile entity to InterestProfileDTO.

    Excludes: id, config_id, created_at, updated_at, relationships
    """
    return InterestProfileDTO(
        keywords=profile.keywords,
        relevance_threshold=profile.relevance_threshold,
        boost_factor=profile.boost_factor,
    )


# Composite Mappers
def complete_digest_config_to_dto(
    config: DigestConfiguration,
    sources: list[ContentSource],
    profile: InterestProfile,
) -> CompleteDigestConfigDTO:
    """
    Convert complete digest configuration to composite DTO.

    Combines config, sources, and interest profile into single response.
    """
    return CompleteDigestConfigDTO(
        config=digest_config_to_dto(config),
        sources=content_sources_to_dtos(sources),
        interest_profile=interest_profile_to_dto(profile),
    )
