"""Data Transfer Objects for API and service layer communication."""

from app.dtos.auth import LoginDTO, RegisterUserDTO, TokenDTO, UserAuthDTO
from app.dtos.base import FrozenDTO
from app.dtos.config import (
    ContentSourceDTO,
    CreateContentSourceDTO,
    DigestConfigDTO,
    InterestProfileDTO,
    UpdateDigestSettingsDTO,
    UpdateInterestKeywordsDTO,
)
from app.dtos.user import UpdateTimezoneDTO, UserDTO

__all__ = [  # noqa: RUF022
    # Base
    "FrozenDTO",
    # Auth DTOs
    "RegisterUserDTO",
    "LoginDTO",
    "TokenDTO",
    "UserAuthDTO",
    # User DTOs
    "UserDTO",
    "UpdateTimezoneDTO",
    # Config DTOs
    "DigestConfigDTO",
    "ContentSourceDTO",
    "InterestProfileDTO",
    "CreateContentSourceDTO",
    "UpdateDigestSettingsDTO",
    "UpdateInterestKeywordsDTO",
]
