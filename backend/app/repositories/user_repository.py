"""Repository for user data access operations."""

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import User


class UserRepository:
    """Repository for user CRUD operations following the repository pattern."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch a user by their ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by their email address (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def create(self, user: User) -> User:
        """
        Create a new user in the database.

        Note: Caller must commit the session.
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """
        Update an existing user in the database.

        Note: Caller must commit the session.
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
