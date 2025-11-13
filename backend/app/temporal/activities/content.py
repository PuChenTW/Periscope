"""Content fetching and configuration activities for Temporal workflows.

This module contains Temporal activities for retrieving user configuration
and fetching content sources needed for digest generation.
"""

from datetime import UTC, datetime

from loguru import logger
from temporalio import activity

import app.temporal.activities.schemas as sc
from app.database import get_async_sessionmaker
from app.exceptions import ValidationError
from app.repositories.config_repository import ConfigRepository


class ContentActivities:
    """Activity class for content and configuration operations."""

    def __init__(self):
        """Initialize shared dependencies."""
        self.async_session_maker = get_async_sessionmaker()

    @activity.defn
    async def fetch_user_config(self, request: sc.FetchUserConfigRequest) -> sc.FetchUserConfigResult:
        """Fetch complete user configuration for digest generation.

        This activity retrieves the user's digest configuration, content sources,
        and interest profile in a single transaction. It's idempotent and
        safe to retry.

        Args:
            request: FetchUserConfigRequest with user_id

        Returns:
            FetchUserConfigResult with complete configuration

        Raises:
            ValidationError: If user or config not found
        """
        start_ts = datetime.now(UTC)
        logger.info(f"Fetching config for user {request.user_id}")

        async with self.async_session_maker() as session:
            repo = ConfigRepository(session)

            # Fetch user and digest config
            user, config = await repo.get_user_with_config(request.user_id)

            if not user:
                raise ValidationError(f"User {request.user_id} not found")

            if not config or not config.is_active:
                raise ValidationError(f"No active digest config for user {request.user_id}")

            # Fetch sources and interest profile
            sources = await repo.get_sources_for_config(config.id)
            profile = await repo.get_interest_profile(config.id)

            if not profile:
                raise ValidationError(f"No interest profile for user {request.user_id}")

            # Build result
            sources_config = [
                sc.ContentSourceConfig(
                    id=source.id,
                    source_type=source.source_type,
                    source_url=source.source_url,
                    source_name=source.source_name,
                    is_active=source.is_active,
                )
                for source in sources
            ]

            profile_config = sc.InterestProfileConfig(
                id=profile.id,
                keywords=profile.keywords,
                relevance_threshold=profile.relevance_threshold,
                boost_factor=profile.boost_factor,
            )

            user_config = sc.DigestUserConfig(
                user_id=user.id,
                email=user.email,
                timezone=user.timezone,
                delivery_time=config.delivery_time,
                summary_style=config.summary_style,
                is_active=config.is_active,
                sources=sources_config,
                interest_profile=profile_config,
            )

            end_ts = datetime.now(UTC)

            result = sc.FetchUserConfigResult(
                user_config=user_config,
                sources_count=len(sources),
                keywords_count=len(profile.keywords),
                start_timestamp=start_ts,
                end_timestamp=end_ts,
            )

            logger.info(
                f"Fetched config for user {request.user_id}: {len(sources)} sources, {len(profile.keywords)} keywords"
            )

            return result
