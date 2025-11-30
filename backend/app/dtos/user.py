"""User profile-related DTOs."""

from pydantic import EmailStr

from app.dtos.base import FrozenDTO


class UserDTO(FrozenDTO):
    """
    Output DTO for user profile data.

    Excludes sensitive fields and internal database details.
    """

    id: str
    email: EmailStr
    timezone: str
    is_verified: bool
    is_active: bool


class UpdateTimezoneDTO(FrozenDTO):
    """Input DTO for updating user timezone."""

    timezone: str
