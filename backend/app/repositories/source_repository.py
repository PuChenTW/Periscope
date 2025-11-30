"""Repository for ContentSource data access operations."""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import ContentSource


class ContentSourceRepository:
    """Repository for content source CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, source_id: str) -> ContentSource | None:
        """Fetch a content source by ID."""
        stmt = select(ContentSource).where(ContentSource.id == source_id)
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def get_active_content_for_config(self, config_id: str) -> list[ContentSource]:
        """Fetch all active content sources for a digest configuration."""
        stmt = select(ContentSource).where(
            ContentSource.config_id == config_id,
            ContentSource.is_active,
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def create(self, source: ContentSource) -> ContentSource:
        """
        Create a new content source.

        Note: Caller must commit the session.
        """
        self.session.add(source)
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def delete(self, source: ContentSource) -> None:
        """
        Delete a content source.

        Note: Caller must commit the session.
        """
        await self.session.delete(source)
