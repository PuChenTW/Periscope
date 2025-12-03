"""Base class for all DTOs using Pydantic frozen models."""

from pydantic import BaseModel, ConfigDict


class FrozenBase(BaseModel):
    """
    Base class for all DTOs using Pydantic frozen models.

    Benefits:
    - Immutable by default (frozen=True)
    - Automatic validation
    - JSON serialization
    - Better FastAPI integration
    """

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
    )
