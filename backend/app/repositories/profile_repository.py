"""
Repository for InterestProfile data access.

Provides database operations for fetching and managing user interest profiles.
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import InterestProfile


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, profile_id: str) -> InterestProfile | None:
        statement = select(InterestProfile).where(InterestProfile.id == profile_id)
        result = await self.session.exec(statement)
        return result.one_or_none()

    async def get_by_config_id(self, config_id: str) -> InterestProfile | None:
        statement = select(InterestProfile).where(InterestProfile.config_id == config_id)
        result = await self.session.exec(statement)
        return result.one_or_none()

    async def update(self, profile: InterestProfile) -> InterestProfile:
        """
        Update an existing interest profile.

        Note: Caller must commit the session.
        """
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
