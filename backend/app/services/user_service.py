"""User profile management service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.dtos.mappers import user_to_dto
from app.dtos.user import UpdateProfileRequest, UserResponse
from app.models.users import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Service for user profile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def update_timezone(self, user: User, update_dto: UpdateProfileRequest) -> UserResponse:
        """
        Update user timezone setting.

        Args:
            user: User instance to update
            update_dto: Timezone update data

        Returns:
            UserDTO with updated timezone (excludes sensitive fields)

        Note: Commits the transaction.
        """
        user.timezone = update_dto.timezone
        updated_user = await self.user_repo.update(user)
        await self.session.commit()
        await self.session.refresh(updated_user)
        return user_to_dto(updated_user)
