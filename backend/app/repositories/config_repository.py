"""Repository for DigestConfiguration and related data access."""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import (
    ContentSource,
    DigestConfiguration,
    InterestProfile,
    User,
)


class ConfigRepository:
    """Access DigestConfiguration, sources, and interest profiles."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_with_config(self, user_id: str) -> tuple[User | None, DigestConfiguration | None]:
        """Fetch user and their digest configuration in a single query.

        Returns (user, config) tuple, either or both may be None.
        """
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.session.exec(user_stmt)
        user = user_result.one_or_none()

        if not user:
            return None, None

        config_stmt = select(DigestConfiguration).where(DigestConfiguration.user_id == user_id)
        config_result = await self.session.exec(config_stmt)
        config = config_result.one_or_none()

        return user, config

    async def get_sources_for_config(self, config_id: str) -> list[ContentSource]:
        """Fetch all active content sources for a config."""
        stmt = select(ContentSource).where(
            ContentSource.config_id == config_id,
            ContentSource.is_active,
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def get_interest_profile(self, config_id: str) -> InterestProfile | None:
        """Fetch interest profile for a config."""
        stmt = select(InterestProfile).where(InterestProfile.config_id == config_id)
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def get_by_user_id(self, user_id: str) -> DigestConfiguration | None:
        """Fetch digest configuration by user ID."""
        stmt = select(DigestConfiguration).where(DigestConfiguration.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def update(self, config: DigestConfiguration) -> DigestConfiguration:
        """
        Update an existing digest configuration.

        Note: Caller must commit the session.
        """
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config
