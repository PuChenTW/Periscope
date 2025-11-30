"""Authentication-related DTOs for registration, login, and token operations."""

from pydantic import EmailStr, Field

from app.dtos.base import FrozenDTO


class RegisterUserDTO(FrozenDTO):
    """Input DTO for user registration."""

    email: EmailStr
    password: str = Field(min_length=8)
    timezone: str = Field(default="UTC")


class LoginDTO(FrozenDTO):
    """Input DTO for user login."""

    email: EmailStr
    password: str


class TokenDTO(FrozenDTO):
    """Output DTO for authentication token."""

    access_token: str
    token_type: str = Field(default="bearer")


class UserAuthDTO(FrozenDTO):
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
