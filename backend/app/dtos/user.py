"""User profile-related DTOs."""

from pydantic import EmailStr
from pydantic_extra_types.timezone_name import TimeZoneName

from app.dtos.base import FrozenBase


class UserResponse(FrozenBase):
    """
    Output DTO for user profile data.

    Excludes sensitive fields and internal database details.
    """

    id: str
    email: EmailStr
    timezone: str
    is_verified: bool
    is_active: bool


class UpdateTimezoneRequest(FrozenBase):
    """Input DTO for updating user timezone."""

    timezone: TimeZoneName
