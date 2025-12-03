"""Authentication-related DTOs for registration, login, and token operations."""

from pydantic import EmailStr, Field
from pydantic_extra_types.timezone_name import TimeZoneName

from app.dtos.base import FrozenBase


class RegisterUserRequest(FrozenBase):
    """Input DTO for user registration."""

    email: EmailStr
    password: str = Field(min_length=8)
    timezone: TimeZoneName = Field(default="UTC")


class LoginRequest(FrozenBase):
    """Input DTO for user login."""

    email: EmailStr
    password: str


class TokenResponse(FrozenBase):
    """Output DTO for authentication token."""

    access_token: str
    token_type: str = Field(default="bearer")


class UserAuthResponse(FrozenBase):
    """
    Output DTO for authenticated user data.

    Returned after registration or login.
    Excludes sensitive fields like hashed_password.
    """

    id: str
    email: EmailStr
    timezone: str
    is_verified: bool
    is_active: bool
