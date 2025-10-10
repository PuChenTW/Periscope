"""
Similarity detection and grouping engine for articles using PydanticAI.

This module provides AI-powered semantic analysis to detect similar articles from
different sources and group them together based on content similarity.
"""

import hashlib
import json
import textwrap
from datetime import UTC, datetime

from loguru import logger
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article
from app.utils.cache import CacheProtocol


class SimilarityScore(BaseModel):
    """AI-determined similarity score with reasoning.

    The confidence score follows this rubric:
    - 0.9-1.0: Nearly identical articles (same event, same sources, slightly different wording)
    - 0.7-0.89: Very similar articles (same core topic/event, different perspectives or details)
    - 0.5-0.69: Somewhat related (related topics, but different focus or angles)
    - 0.3-0.49: Loosely related (same broad category, different specific topics)
    - 0.0-0.29: Not similar (completely different topics)
    """

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Similarity confidence score from 0.0 to 1.0. "
            "Use 0.9+ for nearly identical articles, 0.7-0.89 for very similar, "
            "0.5-0.69 for somewhat related, 0.3-0.49 for loosely related, "
            "and 0.0-0.29 for unrelated articles."
        ),
    )
    reasoning: str = Field(description="Brief explanation of the similarity assessment")


class ArticleGroup(BaseModel):
    """A group of similar articles with metadata."""

    primary_article: Article = Field(description="The main/representative article of the group")
    similar_articles: list[Article] = Field(default_factory=list, description="Other similar articles in the group")
    common_topics: list[str] = Field(default_factory=list, description="Common topics across all articles")
    group_id: str = Field(description="Unique identifier for this group")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SimilarityDetector:
    """
    Detects and groups similar articles using PydanticAI.

    This class uses AI-powered semantic analysis to compare articles and identify
    those that cover similar topics or events, even if they use different wording.
    The AI provider is configurable through application settings.
    """

    def __init__(
        self,
        cache: CacheProtocol,
        settings: Settings | None = None,
        ai_provider: AIProvider | None = None,
    ):
        """
        Initialize the similarity detector with PydanticAI agent.

        Args:
            cache: Cache instance for storing similarity results
            settings: Application settings (uses get_settings() if not provided)
            ai_provider: AI provider instance (creates from settings if not provided)
        """
        self.settings = settings or get_settings()
        self.cache = cache

        # Create AI provider if not injected
        provider = ai_provider or create_ai_provider(self.settings)

        # Initialize PydanticAI agent using the provider
        self.agent = provider.create_agent(
            output_type=SimilarityScore,
            system_prompt=(
                "You are an expert at analyzing news articles and blog posts to assess their similarity. "
                "Compare articles based on:\n"
                "1. Core subject matter and main topic\n"
                "2. Key entities mentioned (people, organizations, places)\n"
                "3. Events or developments discussed\n"
                "4. Overall theme and context\n\n"
                "Provide a confidence score following this rubric:\n"
                "- 0.9-1.0: Nearly identical articles covering the exact same event/topic from the same sources, "
                "with only minor wording differences. Example: Two articles about 'Apple announces iPhone 16' "
                "with the same key details.\n"
                "- 0.7-0.89: Very similar articles about the same core topic or event but with different "
                "perspectives, additional details, or analysis. Example: One article on 'iPhone 16 release' "
                "and another on 'Apple's latest iPhone features'.\n"
                "- 0.5-0.69: Somewhat related articles covering related topics but with different primary focus. "
                "Example: 'iPhone 16 release' vs 'Apple stock rises after product launch'.\n"
                "- 0.3-0.49: Loosely related articles in the same broad category but different specific topics. "
                "Example: 'iPhone 16 release' vs 'Samsung Galaxy update'.\n"
                "- 0.0-0.29: Not similar - completely different topics even if in same general domain. "
                "Example: 'iPhone 16 release' vs 'Google Search algorithm update'.\n\n"
                "IMPORTANT: Score based on content overlap and topical similarity, not just broad category membership."
            ),
        )

    async def detect_similar_articles(self, articles: list[Article]) -> list[ArticleGroup]:
        """
        Detect similar articles and group them together.

        Args:
            articles: List of articles to analyze for similarity

        Returns:
            List of article groups, where each group contains similar articles
        """
        if len(articles) <= 1:
            # No grouping needed for single article
            if articles:
                return [
                    ArticleGroup(
                        primary_article=articles[0],
                        similar_articles=[],
                        common_topics=sorted(articles[0].ai_topics) if articles[0].ai_topics else [],
                        group_id=self._generate_group_id([articles[0]]),
                    )
                ]
            return []

        logger.info(f"Detecting similarity among {len(articles)} articles")

        # Build similarity graph
        similarity_graph: dict[int, list[int]] = {i: [] for i in range(len(articles))}

        # Compare articles pairwise
        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                is_similar = await self._compare_articles(articles[i], articles[j])

                if is_similar:
                    similarity_graph[i].append(j)
                    similarity_graph[j].append(i)

        # Create groups from similarity graph using connected components
        groups = self._create_groups(articles, similarity_graph)

        logger.info(f"Created {len(groups)} article groups from {len(articles)} articles")
        return groups

    async def _compare_articles(self, article1: Article, article2: Article) -> bool:
        """
        Compare two articles for similarity using AI.

        Args:
            article1: First article to compare
            article2: Second article to compare

        Returns:
            Boolean indicating if articles are similar (confidence >= threshold)
        """
        # Check cache first
        cache_key = self._generate_cache_key(article1, article2)
        cached_result = await self._get_cached_similarity(cache_key)
        if cached_result is not None:
            return cached_result

        # Prepare comparison prompt
        prompt = self._build_comparison_prompt(article1, article2)

        try:
            # Run AI comparison
            result = await self.agent.run(prompt)
            similarity_score = result.output

            # Determine if articles are similar based on confidence threshold
            is_similar = similarity_score.confidence >= self.settings.similarity.threshold

            logger.debug(
                f"Compared articles: '{article1.title[:50]}...' vs '{article2.title[:50]}...' "
                f"-> Similar: {is_similar} (confidence: {similarity_score.confidence:.2f}, "
                f"threshold: {self.settings.similarity.threshold:.2f})"
            )

            # Cache the result
            await self._cache_similarity(cache_key, is_similar)

            return is_similar

        except Exception as e:
            logger.error(f"Error comparing articles: {e}")
            # On error, assume not similar to avoid false grouping
            return False

    def _build_comparison_prompt(self, article1: Article, article2: Article) -> str:
        """Build prompt for AI comparison."""
        # Truncate content to avoid token limits (use first 500 chars)
        content1 = article1.content[:500] if article1.content else ""
        content2 = article2.content[:500] if article2.content else ""

        return textwrap.dedent(f"""\
            Article 1:
            Title: {article1.title}
            Content: {content1}
            Tags: {", ".join(article1.tags) if article1.tags else "None"}

            Article 2:
            Title: {article2.title}
            Content: {content2}
            Tags: {", ".join(article2.tags) if article2.tags else "None"}

            Are these articles covering the same story, topic, or event?
        """)

    def _create_groups(
        self,
        articles: list[Article],
        similarity_graph: dict[int, list[int]],
    ) -> list[ArticleGroup]:
        """
        Create article groups from similarity graph using connected components algorithm.

        Args:
            articles: Original list of articles
            similarity_graph: Graph where edges represent similar articles

        Returns:
            List of article groups
        """
        visited = set()
        groups = []

        def dfs(node: int, component: list[int]) -> None:
            """Depth-first search to find connected component."""
            visited.add(node)
            component.append(node)
            for neighbor in similarity_graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, component)

        # Find all connected components
        for i in range(len(articles)):
            if i not in visited:
                component: list[int] = []
                dfs(i, component)

                # Create article group
                component_articles = [articles[idx] for idx in component]

                # Choose primary article (e.g., most recent or first one)
                primary_article = component_articles[0]
                similar_articles = component_articles[1:] if len(component_articles) > 1 else []

                # Merge ai_topics from all articles in the group
                topics_set: set[str] = set()
                for article in component_articles:
                    if article.ai_topics:
                        topics_set.update(article.ai_topics)

                group = ArticleGroup(
                    primary_article=primary_article,
                    similar_articles=similar_articles,
                    common_topics=sorted(topics_set),  # Sort for consistent ordering
                    group_id=self._generate_group_id(component_articles),
                )

                groups.append(group)

        return groups

    def _generate_group_id(self, articles: list[Article]) -> str:
        """Generate unique ID for article group based on article URLs."""
        urls = sorted([str(article.url) for article in articles])
        combined = "|".join(urls)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _generate_cache_key(self, article1: Article, article2: Article) -> str:
        """Generate cache key for article pair."""
        # Sort URLs to ensure consistent cache key regardless of order
        urls = sorted([str(article1.url), str(article2.url)])
        combined = f"similarity:{urls[0]}|{urls[1]}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def _get_cached_similarity(self, cache_key: str) -> bool | None:
        """Retrieve cached similarity result."""
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                data = json.loads(cached)
                return data["is_similar"]
        except Exception as e:
            logger.warning(f"Error retrieving cached similarity: {e}")
        return None

    async def _cache_similarity(self, cache_key: str, is_similar: bool) -> None:
        """Cache similarity result."""
        try:
            ttl_seconds = self.settings.similarity.cache_ttl_minutes * 60
            data = {"is_similar": is_similar}
            await self.cache.setex(cache_key, ttl_seconds, json.dumps(data))
        except Exception as e:
            logger.warning(f"Error caching similarity result: {e}")


if __name__ == "__main__":
    import asyncio

    from pydantic import HttpUrl

    from app.utils.cache import RedisCache
    from app.utils.redis_client import get_redis_client

    async def main():
        # Create test articles
        article1 = Article(
            url=HttpUrl("https://example.com/article1"),
            title="OpenAI Releases GPT-5 with Major Performance Improvements",
            content=(
                "OpenAI announced today the release of GPT-5, their latest language model. "
                "The new model shows significant improvements in reasoning and accuracy compared to GPT-4. "
                "The company claims 40% better performance on complex tasks."
            ),
            tags=["AI", "technology"],
            ai_topics=["artificial intelligence", "machine learning"],
        )

        article2 = Article(
            url=HttpUrl("https://example.com/article2"),
            title="GPT-5 Launch: OpenAI's Newest AI Model Shows Dramatic Gains",
            content=(
                "In a major announcement, OpenAI has unveiled GPT-5. "
                "The advanced language model demonstrates remarkable improvements in task completion "
                "and reasoning abilities over its predecessor GPT-4."
            ),
            tags=["AI", "tech news"],
            ai_topics=["artificial intelligence", "language models"],
        )

        article3 = Article(
            url=HttpUrl("https://example.com/article3"),
            title="New Python 3.13 Released with Performance Enhancements",
            content=(
                "The Python Software Foundation released Python 3.13 today. "
                "The new version includes significant performance improvements and new syntax features for developers."
            ),
            tags=["Python", "programming"],
            ai_topics=["programming languages", "software development"],
        )

        # Initialize detector with cache
        redis = await get_redis_client()
        cache = RedisCache(redis_client=redis)
        detector = SimilarityDetector(cache=cache)

        # Test similarity detection
        print("\n=== Testing Similarity Detection ===\n")
        groups = await detector.detect_similar_articles([article1, article2, article3])

        print(f"Found {len(groups)} group(s):\n")
        for i, group in enumerate(groups, 1):
            print(f"Group {i} (ID: {group.group_id}):")
            print(f"  Primary: {group.primary_article.title}")
            print(f"  Similar articles: {len(group.similar_articles)}")
            for article in group.similar_articles:
                print(f"    - {article.title}")
            print(f"  Common topics: {', '.join(group.common_topics)}")
            print()

    asyncio.run(main())
