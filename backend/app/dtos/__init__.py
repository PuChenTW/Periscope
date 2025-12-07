"""Data Transfer Objects for API and service layer communication."""

from app.dtos.auth import LoginRequest, RegisterUserRequest, TokenResponse, UserAuthResponse
from app.dtos.base import FrozenBase
from app.dtos.config import (
    ContentSourceResponse,
    CreateContentSourceRequest,
    DigestConfigResponse,
    InterestProfileResponse,
    UpdateDigestSettingsRequest,
    UpdateInterestKeywordsRequest,
)
from app.dtos.user import UpdateProfileRequest, UserResponse

__all__ = [  # noqa: RUF022
    # Base
    "FrozenBase",
    # Auth DTOs
    "RegisterUserRequest",
    "LoginRequest",
    "TokenResponse",
    "UserAuthResponse",
    # User DTOs
    "UserResponse",
    "UpdateProfileRequest",
    # Config DTOs
    "DigestConfigResponse",
    "ContentSourceResponse",
    "InterestProfileResponse",
    "CreateContentSourceRequest",
    "UpdateDigestSettingsRequest",
    "UpdateInterestKeywordsRequest",
]
