"""
Repository for InterestProfile data access.

Provides database operations for fetching and managing user interest profiles.
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import InterestProfile


class ProfileRepository:
    """Repository for InterestProfile database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLModel async session for database operations
        """
        self.session = session

    async def get_by_id(self, profile_id: str) -> InterestProfile | None:
        """
        Fetch interest profile by ID.

        Args:
            profile_id: Unique identifier for the interest profile

        Returns:
            InterestProfile if found, None otherwise
        """
        statement = select(InterestProfile).where(InterestProfile.id == profile_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_config_id(self, config_id: str) -> InterestProfile | None:
        """
        Fetch interest profile by digest configuration ID.

        Args:
            config_id: Digest configuration ID

        Returns:
            InterestProfile if found, None otherwise
        """
        statement = select(InterestProfile).where(InterestProfile.config_id == config_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
