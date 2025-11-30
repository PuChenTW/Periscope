"""Authentication and user registration service."""

from datetime import time

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dtos.auth import LoginDTO, RegisterUserDTO, TokenDTO, UserAuthDTO
from app.dtos.mappers import user_to_auth_dto
from app.models.users import DigestConfiguration, InterestProfile, User
from app.repositories.user_repository import UserRepository
from app.utils.auth import create_access_token, get_password_hash, verify_password


class AuthService:
    """Service for authentication and registration operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_user(self, register_dto: RegisterUserDTO) -> UserAuthDTO:
        """
        Register new user with default configuration and interest profile.

        Multi-step transaction:
        1. Check email not already registered
        2. Create user with hashed password
        3. Create default DigestConfiguration
        4. Create empty InterestProfile
        5. Commit all or rollback

        Args:
            register_dto: Registration data (email, password, timezone)

        Returns:
            UserAuthDTO with created user data (excludes sensitive fields)

        Raises:
            HTTPException: 409 if email already registered

        Note: Commits the transaction.
        """
        email = register_dto.email.lower()

        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        new_user = User(
            email=email,
            hashed_password=get_password_hash(register_dto.password),
            timezone=register_dto.timezone,
            is_verified=False,
            is_active=True,
        )
        created_user = await self.user_repo.create(new_user)

        default_config = DigestConfiguration(
            user_id=created_user.id,
            delivery_time=time(7, 0),
            summary_style="brief",
            is_active=True,
        )
        self.session.add(default_config)
        await self.session.flush()

        default_profile = InterestProfile(
            config_id=default_config.id,
            keywords=[],
            relevance_threshold=40,
            boost_factor=1.0,
        )
        self.session.add(default_profile)

        await self.session.commit()
        await self.session.refresh(created_user)

        return user_to_auth_dto(created_user)

    async def authenticate_user(self, login_dto: LoginDTO) -> tuple[UserAuthDTO, TokenDTO]:
        """
        Authenticate user and return access token.

        Args:
            login_dto: Login credentials (email, password)

        Returns:
            Tuple of (UserAuthDTO, TokenDTO)

        Raises:
            HTTPException: 401 if invalid credentials or inactive account
        """
        email = login_dto.email.lower()
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(login_dto.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        access_token = create_access_token(user_id=user.id, email=user.email)
        token_dto = TokenDTO(access_token=access_token)

        return user_to_auth_dto(user), token_dto
