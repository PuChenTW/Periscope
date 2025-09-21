from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(datetime.UTC)


class BaseModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = Field(
        default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now}
    )
