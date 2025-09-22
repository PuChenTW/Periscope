from datetime import datetime

from sqlmodel import Field, func
from ulid import ULID


def utc_now() -> datetime:
    return datetime.now(datetime.UTC)


class ULIDMixedIn:
    """The MixedIn model for ULID as the primary key"""

    id: str = Field(primary_key=True, default_factory=lambda: str(ULID()))


class ActiveLifecycleTimestampMixin:
    """MixedIn model create and update for timestamp"""

    created_at: datetime = Field(
        default_factory=utc_now,
        description="The timestamp when the record is created",
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        description="The timestamp when the record is updated",
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": utc_now,
        },
    )
