"""Digest configuration management service."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dtos.config import (
    CompleteDigestConfigDTO,
    ContentSourceDTO,
    CreateContentSourceDTO,
    DigestConfigDTO,
    InterestProfileDTO,
    UpdateDigestSettingsDTO,
    UpdateInterestKeywordsDTO,
)
from app.dtos.mappers import (
    complete_digest_config_to_dto,
    content_source_to_dto,
    digest_config_to_dto,
    interest_profile_to_dto,
)
from app.models.users import ContentSource
from app.repositories.config_repository import ConfigRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.source_repository import ContentSourceRepository


class ConfigService:
    """Service for digest configuration, sources, and interest profile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_repo = ConfigRepository(session)
        self.source_repo = ContentSourceRepository(session)
        self.profile_repo = ProfileRepository(session)

    async def get_user_config(self, user_id: str) -> CompleteDigestConfigDTO:
        """
        Fetch complete configuration for user.

        Args:
            user_id: User ID to fetch config for

        Returns:
            CompleteDigestConfigDTO containing config, sources, and interest profile

        Raises:
            HTTPException: 404 if config not found
        """
        _, config = await self.config_repo.get_user_with_config(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digest configuration not found",
            )

        sources = await self.source_repo.get_active_content_for_config(config.id)
        profile = await self.config_repo.get_interest_profile(config.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interest profile not found",
            )

        return complete_digest_config_to_dto(config, sources, profile)

    async def update_digest_settings(
        self,
        user_id: str,
        update_dto: UpdateDigestSettingsDTO,
    ) -> DigestConfigDTO:
        """
        Update digest configuration settings.

        Args:
            user_id: User ID
            update_dto: Digest settings update data

        Returns:
            DigestConfigDTO with updated settings

        Raises:
            HTTPException: 404 if config not found

        Note: Commits the transaction.
        """
        config = await self.config_repo.get_by_user_id(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digest configuration not found",
            )

        config.delivery_time = update_dto.delivery_time
        config.summary_style = update_dto.summary_style
        config.is_active = update_dto.is_active

        updated_config = await self.config_repo.update(config)
        await self.session.commit()
        await self.session.refresh(updated_config)

        return digest_config_to_dto(updated_config)

    async def add_content_source(
        self,
        user_id: str,
        create_dto: CreateContentSourceDTO,
    ) -> ContentSourceDTO:
        """
        Add new content source to user's configuration.

        Args:
            user_id: User ID
            create_dto: Content source creation data

        Returns:
            ContentSourceDTO with created source data

        Raises:
            HTTPException: 404 if config not found

        Note: Commits the transaction.
        """
        config = await self.config_repo.get_by_user_id(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digest configuration not found",
            )

        new_source = ContentSource(
            config_id=config.id,
            source_type=create_dto.source_type,
            source_url=str(create_dto.source_url),
            source_name=create_dto.source_name,
            is_active=True,
        )

        created_source = await self.source_repo.create(new_source)
        await self.session.commit()
        await self.session.refresh(created_source)

        return content_source_to_dto(created_source)

    async def remove_content_source(self, user_id: str, source_id: str) -> None:
        """
        Remove content source from user's configuration.

        Args:
            user_id: User ID (for ownership verification)
            source_id: Source ID to remove

        Raises:
            HTTPException: 404 if config or source not found

        Note: Commits the transaction.
        """
        config = await self.config_repo.get_by_user_id(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digest configuration not found",
            )

        sources = await self.source_repo.get_active_content_for_config(config.id)
        source_to_delete = next((s for s in sources if s.id == source_id), None)

        if not source_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content source not found",
            )

        await self.source_repo.delete(source_to_delete)
        await self.session.commit()

    async def update_interest_keywords(
        self,
        user_id: str,
        update_dto: UpdateInterestKeywordsDTO,
    ) -> InterestProfileDTO:
        """
        Update user's interest profile keywords.

        Args:
            user_id: User ID
            update_dto: Interest keywords update data

        Returns:
            InterestProfileDTO with updated keywords

        Raises:
            HTTPException: 400 if too many keywords, 404 if config/profile not found

        Note: Commits the transaction.
        """
        config = await self.config_repo.get_by_user_id(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digest configuration not found",
            )

        profile = await self.config_repo.get_interest_profile(config.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interest profile not found",
            )

        if len(update_dto.keywords) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 keywords allowed",
            )

        profile.keywords = update_dto.keywords

        updated_profile = await self.profile_repo.update(profile)
        await self.session.commit()
        await self.session.refresh(updated_profile)

        return interest_profile_to_dto(updated_profile)
