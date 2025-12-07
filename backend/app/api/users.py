"""User management and profile configuration API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dtos.config import (
    ContentSourceResponse,
    CreateContentSourceRequest,
    DigestConfigResponse,
    InterestProfileUpdateRequest,
    UpdateDigestSettingsRequest,
    UpdateInterestKeywordsRequest,
)
from app.dtos.user import UpdateProfileRequest, UserResponse
from app.models.users import User
from app.services.config_service import ConfigService
from app.services.user_service import UserService
from app.utils.auth import get_current_user

router = APIRouter()


# User Profile Endpoints
@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's profile information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        timezone=current_user.timezone,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
    )


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_update: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Update current user's timezone setting."""
    user_service = UserService(session)
    user_dto = await user_service.update_timezone(current_user, profile_update)

    return UserResponse(
        id=user_dto.id,
        email=user_dto.email,
        timezone=user_dto.timezone,
        is_verified=user_dto.is_verified,
        is_active=user_dto.is_active,
    )


# Digest Configuration Endpoints
@router.get("/config", response_model=DigestConfigResponse)
async def get_digest_config(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Get user's digest configuration including sources and interest profile."""
    config_service = ConfigService(session)
    complete_config_dto = await config_service.get_user_config(current_user.id)

    keywords_str = (
        ", ".join(complete_config_dto.interest_profile.keywords)
        if complete_config_dto.interest_profile.keywords
        else ""
    )

    return DigestConfigResponse(
        delivery_time=complete_config_dto.config.delivery_time.isoformat(),
        summary_style=complete_config_dto.config.summary_style,
        is_active=complete_config_dto.config.is_active,
        sources=complete_config_dto.sources,
        interest_profile={"keywords": keywords_str},
    )


@router.put("/config", response_model=dict)
async def update_digest_config(
    config_update: UpdateDigestSettingsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Update user's digest configuration settings."""
    config_service = ConfigService(session)
    config_dto = await config_service.update_digest_settings(current_user.id, config_update)

    return {
        "message": "Digest configuration updated successfully",
        "config": {
            "delivery_time": config_dto.delivery_time.isoformat(),
            "summary_style": config_dto.summary_style,
            "is_active": config_dto.is_active,
        },
    }


# Content Source Endpoints
@router.post("/sources", response_model=ContentSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_content_source(
    source_data: CreateContentSourceRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Add a new content source to user's digest configuration."""
    config_service = ConfigService(session)
    source_dto = await config_service.add_content_source(current_user.id, source_data)

    return ContentSourceResponse(
        id=source_dto.id,
        source_type=source_dto.source_type,
        source_url=source_dto.source_url,
        source_name=source_dto.source_name,
        is_active=source_dto.is_active,
    )


@router.delete("/sources/{source_id}", status_code=status.HTTP_200_OK)
async def remove_content_source(
    source_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Remove a content source from user's digest configuration."""
    config_service = ConfigService(session)
    await config_service.remove_content_source(
        user_id=current_user.id,
        source_id=source_id,
    )

    return {"message": f"Content source {source_id} removed successfully"}


# Interest Profile Endpoint
@router.put("/interest-profile", response_model=dict)
async def update_interest_profile(
    profile_update: InterestProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Update user's interest profile keywords."""
    config_service = ConfigService(session)
    keywords_list = [kw.strip() for kw in profile_update.keywords.split(",") if kw.strip()]
    update_dto = UpdateInterestKeywordsRequest(keywords=keywords_list)
    profile_dto = await config_service.update_interest_keywords(current_user.id, update_dto)

    return {
        "message": "Interest profile updated successfully",
        "keywords": ", ".join(profile_dto.keywords),
    }
