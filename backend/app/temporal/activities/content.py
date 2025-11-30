"""Content fetching and configuration activities for Temporal workflows.

This module contains Temporal activities for retrieving user configuration
and fetching content sources needed for digest generation.
"""

import asyncio
from datetime import UTC, datetime

from loguru import logger
from pydantic import HttpUrl
from temporalio import activity

import app.temporal.activities.schemas as sc
from app.config import get_settings
from app.database import get_async_sessionmaker
from app.exceptions import ValidationError
from app.processors.fetchers.base import FetchResult, SourceInfo, SourceType
from app.processors.fetchers.factory import create_fetcher
from app.repositories.config_repository import ConfigRepository


class ContentActivities:
    """Activity class for content and configuration operations."""

    def __init__(self):
        """Initialize shared dependencies."""
        self.async_session_maker = get_async_sessionmaker()
        self.settings = get_settings()

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

    @activity.defn(name="fetch_sources_parallel")
    async def fetch_sources_parallel(self, request: sc.FetchSourcesParallelRequest) -> sc.FetchSourcesParallelResult:
        """Fetch content from multiple sources in parallel.

        Uses asyncio.gather to fetch from all sources concurrently.
        Gracefully handles partial failures - returns successful articles
        even if some sources fail.

        Idempotency Contract:
        - No caching (raw articles change frequently)
        - Idempotent via fetch timestamp in Article model
        - Safe to retry on failure

        Args:
            request: FetchSourcesParallelRequest with source list

        Returns:
            FetchSourcesParallelResult with articles and metrics

        Activity Options:
            - Timeout: MEDIUM_TIMEOUT (30s)
            - Retry: MEDIUM_RETRY_POLICY (3 attempts, 5s-45s backoff)
            - Idempotent: Yes (via fetch timestamp)
        """
        start_ts = datetime.now(UTC)
        logger.info(f"Fetching from {len(request.sources)} sources in parallel")

        # Filter to active sources only
        active_sources = [s for s in request.sources if s.is_active]

        if not active_sources:
            logger.warning("No active sources to fetch from")
            return sc.FetchSourcesParallelResult(
                articles=[],
                total_sources=0,
                successful_sources=0,
                failed_sources=0,
                total_articles=0,
                fetch_errors={},
                start_timestamp=start_ts,
                end_timestamp=datetime.now(UTC),
            )

        # Create fetch tasks for each source
        fetch_tasks = [self._fetch_single_source(source) for source in active_sources]

        # Execute all fetches in parallel
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Aggregate results
        all_articles = []
        successful_sources = 0
        failed_sources = 0
        fetch_errors: dict[str, str] = {}

        for source, result in zip(active_sources, fetch_results, strict=True):
            if not result.success:
                # Fetch returned failure result
                failed_sources += 1
                fetch_errors[source.id] = result.error_message or "Unknown error"
                logger.warning(f"Source {source.source_name} returned no content: {result.error_message}")
            else:
                # Success
                successful_sources += 1
                all_articles.extend(result.articles)
                logger.info(f"Source {source.source_name} returned {len(result.articles)} articles")

        end_ts = datetime.now(UTC)

        logger.info(
            f"Fetch complete: {successful_sources}/{len(active_sources)} sources successful, "
            f"{len(all_articles)} total articles"
        )

        return sc.FetchSourcesParallelResult(
            articles=all_articles,
            total_sources=len(active_sources),
            successful_sources=successful_sources,
            failed_sources=failed_sources,
            total_articles=len(all_articles),
            fetch_errors=fetch_errors,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
        )

    async def _fetch_single_source(self, source: sc.ContentSourceConfig) -> FetchResult:
        """Fetch content from a single source.

        Helper method that wraps fetcher creation and execution.
        Handles all errors and returns FetchResult.

        Args:
            source: ContentSourceConfig for the source to fetch

        Returns:
            FetchResult with articles or error information
        """
        try:
            # Create fetcher using factory
            source_type = SourceType(source.source_type)
            fetcher = create_fetcher(
                source_type,
                timeout=self.settings.rss.fetch_timeout,
                max_articles=self.settings.rss.max_articles_per_feed,
            )

            # Fetch content
            result = await fetcher.fetch_content(source.source_url)
            return result

        except Exception as e:
            # Return failed result instead of raising
            logger.error(f"Error fetching {source.source_url}: {e}")
            return FetchResult(
                source_info=SourceInfo(
                    title=source.source_name,
                    url=HttpUrl(source.source_url),
                ),
                articles=[],
                fetch_timestamp=datetime.now(UTC),
                success=False,
                error_message=str(e),
            )
