# Test Coverage Implementation Guide

This guide provides concrete examples for implementing the tests outlined in the Test Coverage Enhancement Plan.

## Quick Start

### 1. Test File Template

```python
"""
Unit tests for [activity_name] batch processing activity.

Tests the [activity_name] activity in isolation using mocked dependencies.
Validates caching behavior, error handling, and observability metrics.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.processors.fetchers.base import Article
from app.temporal.activities.schemas import Batch[Activity]Request, Batch[Activity]Result


@pytest.mark.unit
@pytest.mark.asyncio
class Test[Activity]Batch:
    """Unit tests for [activity_name]_batch activity."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for cache operations."""
        client = AsyncMock()
        client.get.return_value = None  # Cache miss by default
        client.setex.return_value = True
        client.delete.return_value = True
        return client

    @pytest.fixture
    def activities(self, mock_redis_client):
        """Create ProcessingActivities instance with mocked dependencies."""
        with patch("app.temporal.activities.processing.get_redis_client", return_value=mock_redis_client):
            with patch("app.temporal.activities.processing.create_ai_provider"):
                from app.temporal.activities.processing import ProcessingActivities
                return ProcessingActivities()

    async def test_happy_path(self, activities, sample_articles):
        """Test successful processing of all articles."""
        # Arrange
        request = Batch[Activity]Request(articles=sample_articles)

        # Act
        result = await activities.[activity_name]_batch(request)

        # Assert
        assert isinstance(result, Batch[Activity]Result)
        assert result.total_processed == len(sample_articles)
        assert result.errors_count == 0
        # Add specific assertions...
```

---

## Phase 1.1: Validation Activity Tests

### Example 1: Happy Path Test

```python
"""tests/test_temporal/test_activities_validation.py"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.processors.fetchers.base import Article
from app.processors.validator import ValidationResult
from app.temporal.activities.schemas import BatchValidationRequest, BatchValidationResult


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidateAndFilterBatch:
    """Unit tests for validate_and_filter_batch activity."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for cache operations."""
        client = AsyncMock()
        client.get.return_value = None  # Cache miss by default
        client.setex.return_value = True
        client.delete.return_value = True
        return client

    @pytest.fixture
    def mock_validator(self):
        """Mock ContentValidator."""
        validator = Mock()
        # Default: all articles valid
        validator.validate_article = AsyncMock(
            return_value=ValidationResult(
                is_empty=False,
                is_too_short=False,
                is_spam=False,
                confidence=0.0,
                validation_message="Valid",
            )
        )
        return validator

    @pytest.fixture
    def activities(self, mock_redis_client, mock_validator):
        """Create ProcessingActivities with mocked dependencies."""
        with patch("app.temporal.activities.processing.get_redis_client", return_value=mock_redis_client):
            with patch("app.temporal.activities.processing.ContentValidator", return_value=mock_validator):
                from app.temporal.activities.processing import ProcessingActivities
                return ProcessingActivities()

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing."""
        return [
            Article(
                title="Article 1",
                url="https://example.com/article1",
                content="This is valid content that meets minimum length requirements.",
                published_date=None,
            ),
            Article(
                title="Article 2",
                url="https://example.com/article2",
                content="Another valid article with sufficient content length.",
                published_date=None,
            ),
        ]

    async def test_validate_batch_happy_path(self, activities, sample_articles):
        """Test successful validation of all articles."""
        # Arrange
        request = BatchValidationRequest(articles=sample_articles)

        # Act
        result = await activities.validate_and_filter_batch(request)

        # Assert
        assert isinstance(result, BatchValidationResult)
        assert result.total_processed == 2
        assert result.valid_count == 2
        assert result.invalid_count == 0
        assert result.errors_count == 0
        assert len(result.validation_results) == 2

        # Verify all articles marked as valid
        for url, validation in result.validation_results.items():
            assert validation.is_valid
            assert validation.validation_message == "Valid"

    async def test_validate_batch_mixed_results(self, activities, mock_validator, sample_articles):
        """Test validation with some articles passing and some failing."""
        # Arrange
        request = BatchValidationRequest(articles=sample_articles)

        # Mock validator to return different results
        valid_result = ValidationResult(
            is_empty=False,
            is_too_short=False,
            is_spam=False,
            confidence=0.0,
            validation_message="Valid",
        )
        spam_result = ValidationResult(
            is_empty=False,
            is_too_short=False,
            is_spam=True,
            confidence=1.0,
            validation_message="Detected as spam",
        )
        mock_validator.validate_article.side_effect = [valid_result, spam_result]

        # Act
        result = await activities.validate_and_filter_batch(request)

        # Assert
        assert result.total_processed == 2
        assert result.valid_count == 1
        assert result.invalid_count == 1

        # Verify first article valid, second spam
        article1_validation = result.validation_results[str(sample_articles[0].url)]
        assert article1_validation.is_valid

        article2_validation = result.validation_results[str(sample_articles[1].url)]
        assert not article2_validation.is_valid
        assert article2_validation.is_spam

    async def test_validate_batch_cache_hit(self, activities, mock_redis_client, sample_articles):
        """Test validation with cached results."""
        # Arrange
        request = BatchValidationRequest(articles=sample_articles)

        # Mock cache hit
        cached_validation = ValidationResult(
            is_empty=False,
            is_too_short=False,
            is_spam=False,
            confidence=0.0,
            validation_message="Valid",
        )
        mock_redis_client.get.return_value = cached_validation.model_dump_json().encode()

        # Act
        result = await activities.validate_and_filter_batch(request)

        # Assert
        assert result.total_processed == 2
        assert result.valid_count == 2

        # Verify cache was checked (get called for each article)
        assert mock_redis_client.get.call_count == 2

        # Verify validator NOT called (cache hit)
        assert activities.validator.validate_article.call_count == 0

    async def test_validate_batch_cache_corruption(self, activities, mock_redis_client, mock_validator, sample_articles):
        """Test validation handles corrupted cache data gracefully."""
        # Arrange
        request = BatchValidationRequest(articles=sample_articles)

        # Mock corrupted cache data (invalid JSON)
        mock_redis_client.get.return_value = b"invalid json data"

        # Act
        result = await activities.validate_and_filter_batch(request)

        # Assert
        assert result.total_processed == 2
        assert result.valid_count == 2

        # Verify cache was deleted after corruption detected
        assert mock_redis_client.delete.call_count == 2

        # Verify validator called after cache corruption
        assert activities.validator.validate_article.call_count == 2

    async def test_validate_batch_empty_input(self, activities):
        """Test validation with empty article list."""
        # Arrange
        request = BatchValidationRequest(articles=[])

        # Act
        result = await activities.validate_and_filter_batch(request)

        # Assert
        assert result.total_processed == 0
        assert result.valid_count == 0
        assert result.invalid_count == 0
        assert result.errors_count == 0
        assert len(result.validation_results) == 0
```

---

## Phase 1.2: Quality Activity Tests

### Example 2: Quality Scoring with Cache

```python
"""tests/test_temporal/test_activities_quality.py"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.processors.fetchers.base import Article
from app.processors.quality_scorer import ContentQualityResult
from app.temporal.activities.schemas import BatchQualityRequest, BatchQualityResult


@pytest.mark.unit
@pytest.mark.asyncio
class TestScoreQualityBatch:
    """Unit tests for score_quality_batch activity."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for cache operations."""
        client = AsyncMock()
        client.get.return_value = None  # Cache miss by default
        client.setex.return_value = True
        return client

    @pytest.fixture
    def mock_quality_scorer(self):
        """Mock QualityScorer."""
        scorer = Mock()
        scorer.calculate_quality_score = AsyncMock(
            return_value=ContentQualityResult(
                quality_score=75,
                metadata_score=50,
                ai_content_score=25,
                breakdown={
                    "has_author": True,
                    "has_published_date": True,
                    "content_length_score": 30,
                    "ai_quality_score": 25,
                },
            )
        )
        return scorer

    @pytest.fixture
    def activities(self, mock_redis_client, mock_quality_scorer):
        """Create ProcessingActivities with mocked dependencies."""
        with patch("app.temporal.activities.processing.get_redis_client", return_value=mock_redis_client):
            with patch("app.temporal.activities.processing.QualityScorer", return_value=mock_quality_scorer):
                from app.temporal.activities.processing import ProcessingActivities
                return ProcessingActivities()

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing."""
        return [
            Article(
                title="High Quality Article",
                url="https://example.com/article1",
                content="Well-written content with good structure and valuable information.",
                published_date=None,
                author="John Doe",
            ),
        ]

    async def test_score_quality_batch_happy_path(self, activities, sample_articles):
        """Test successful quality scoring of all articles."""
        # Arrange
        request = BatchQualityRequest(articles=sample_articles)

        # Act
        result = await activities.score_quality_batch(request)

        # Assert
        assert isinstance(result, BatchQualityResult)
        assert result.total_scored == 1
        assert result.cache_hits == 0
        assert result.errors_count == 0
        assert result.ai_calls == 1

        # Verify quality results
        quality_result = result.quality_results[str(sample_articles[0].url)]
        assert quality_result.quality_score == 75

    async def test_score_quality_batch_cache_hit(self, activities, mock_redis_client, sample_articles):
        """Test quality scoring with cached results."""
        # Arrange
        request = BatchQualityRequest(articles=sample_articles)

        # Mock cache hit
        cached_quality = ContentQualityResult(
            quality_score=80,
            metadata_score=60,
            ai_content_score=20,
            breakdown={},
        )
        mock_redis_client.get.return_value = cached_quality.model_dump_json().encode()

        # Act
        result = await activities.score_quality_batch(request)

        # Assert
        assert result.total_scored == 1
        assert result.cache_hits == 1
        assert result.ai_calls == 0  # No AI calls due to cache hit

        # Verify cached result used
        quality_result = result.quality_results[str(sample_articles[0].url)]
        assert quality_result.quality_score == 80

    async def test_score_quality_batch_ai_failure(self, activities, mock_quality_scorer, sample_articles):
        """Test quality scoring handles AI failure gracefully."""
        # Arrange
        request = BatchQualityRequest(articles=sample_articles)

        # Mock AI failure (returns metadata-only score)
        mock_quality_scorer.calculate_quality_score.return_value = ContentQualityResult(
            quality_score=50,  # Metadata only
            metadata_score=50,
            ai_content_score=0,  # No AI score
            breakdown={},
        )

        # Act
        result = await activities.score_quality_batch(request)

        # Assert
        assert result.total_scored == 1
        assert result.errors_count == 0  # Not an error, just fallback

        # Verify metadata-only scoring
        quality_result = result.quality_results[str(sample_articles[0].url)]
        assert quality_result.quality_score == 50
        assert quality_result.ai_content_score == 0
```

---

## Phase 1.3: Topics Activity Tests

### Example 3: Topic Extraction with Mutation

```python
"""tests/test_temporal/test_activities_topics.py"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.processors.fetchers.base import Article
from app.temporal.activities.schemas import BatchTopicExtractionRequest, BatchTopicExtractionResult


@pytest.mark.unit
@pytest.mark.asyncio
class TestExtractTopicsBatch:
    """Unit tests for extract_topics_batch activity."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for cache operations."""
        client = AsyncMock()
        client.get.return_value = None  # Cache miss by default
        client.setex.return_value = True
        return client

    @pytest.fixture
    def mock_topic_extractor(self):
        """Mock TopicExtractor."""
        extractor = Mock()
        extractor.extract_topics = AsyncMock(
            return_value=["technology", "artificial intelligence", "machine learning"]
        )
        return extractor

    @pytest.fixture
    def activities(self, mock_redis_client, mock_topic_extractor):
        """Create ProcessingActivities with mocked dependencies."""
        with patch("app.temporal.activities.processing.get_redis_client", return_value=mock_redis_client):
            with patch("app.temporal.activities.processing.TopicExtractor", return_value=mock_topic_extractor):
                from app.temporal.activities.processing import ProcessingActivities
                return ProcessingActivities()

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing."""
        return [
            Article(
                title="AI Advances in 2024",
                url="https://example.com/ai-article",
                content="Article about artificial intelligence and machine learning advancements.",
                published_date=None,
            ),
        ]

    async def test_extract_topics_batch_happy_path(self, activities, sample_articles):
        """Test successful topic extraction for all articles."""
        # Arrange
        request = BatchTopicExtractionRequest(articles=sample_articles)

        # Act
        result = await activities.extract_topics_batch(request)

        # Assert
        assert isinstance(result, BatchTopicExtractionResult)
        assert result.total_processed == 1
        assert result.articles_with_topics == 1
        assert result.cache_hits == 0
        assert result.errors_count == 0

        # Verify article mutation (ai_topics populated)
        article_with_topics = result.articles[0]
        assert len(article_with_topics.ai_topics) == 3
        assert "technology" in article_with_topics.ai_topics
        assert "artificial intelligence" in article_with_topics.ai_topics

    async def test_extract_topics_batch_cache_hit(self, activities, mock_redis_client, sample_articles):
        """Test topic extraction with cached results."""
        # Arrange
        request = BatchTopicExtractionRequest(articles=sample_articles)

        # Mock cache hit (comma-separated topics)
        mock_redis_client.get.return_value = b"technology,AI,python"

        # Act
        result = await activities.extract_topics_batch(request)

        # Assert
        assert result.total_processed == 1
        assert result.articles_with_topics == 1
        assert result.cache_hits == 1
        assert result.ai_calls == 0

        # Verify cached topics used
        article_with_topics = result.articles[0]
        assert article_with_topics.ai_topics == ["technology", "AI", "python"]

    async def test_extract_topics_batch_empty_topics(self, activities, mock_topic_extractor, sample_articles):
        """Test topic extraction when no topics found."""
        # Arrange
        request = BatchTopicExtractionRequest(articles=sample_articles)

        # Mock empty topics result
        mock_topic_extractor.extract_topics.return_value = []

        # Act
        result = await activities.extract_topics_batch(request)

        # Assert
        assert result.total_processed == 1
        assert result.articles_with_topics == 0  # No topics found
        assert result.errors_count == 0

        # Verify article has empty topics list
        article_with_topics = result.articles[0]
        assert article_with_topics.ai_topics == []

    async def test_extract_topics_batch_partial_failure(self, activities, mock_topic_extractor, sample_articles):
        """Test topic extraction handles per-article failures gracefully."""
        # Arrange
        # Add second article
        sample_articles.append(
            Article(
                title="Article 2",
                url="https://example.com/article2",
                content="Another article",
                published_date=None,
            )
        )
        request = BatchTopicExtractionRequest(articles=sample_articles)

        # Mock failure for second article
        mock_topic_extractor.extract_topics.side_effect = [
            ["technology"],  # First succeeds
            Exception("AI service unavailable"),  # Second fails
        ]

        # Act
        result = await activities.extract_topics_batch(request)

        # Assert
        assert result.total_processed == 2
        assert result.articles_with_topics == 1  # Only first article
        assert result.errors_count == 1

        # Verify first article has topics
        assert result.articles[0].ai_topics == ["technology"]

        # Verify second article has empty topics (graceful failure)
        assert result.articles[1].ai_topics == []
```

---

## Phase 3.1: End-to-End Integration Test

### Example 4: Full Pipeline Test

```python
"""tests/test_temporal/test_activities_integration.py"""

import pytest
from datetime import UTC, datetime

from app.models import InterestProfile
from app.processors.fetchers.base import Article
from app.temporal.activities.processing import ProcessingActivities
from app.temporal.activities import schemas as sc


@pytest.mark.integration
@pytest.mark.asyncio
class TestActivitiesIntegration:
    """End-to-end integration tests for activity pipeline."""

    @pytest.fixture
    async def profile(self, db_session):
        """Create test interest profile."""
        profile = InterestProfile(
            user_id="test-user",
            keywords=["technology", "AI", "python"],
            relevance_threshold=50,
            boost_factor=1.2,
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        return profile

    @pytest.fixture
    def sample_raw_articles(self):
        """Raw articles for full pipeline test."""
        return [
            Article(
                title="Python AI Framework Released",
                url="https://example.com/python-ai",
                content="A new Python framework for AI development was released today. " * 20,  # Sufficient length
                published_date=datetime.now(UTC),
                author="Jane Doe",
            ),
            Article(
                title="Spam Article",
                url="https://spam.com/spam",
                content="BUY NOW!!! CLICK HERE!!! LIMITED TIME OFFER!!!",  # Spam pattern
                published_date=None,
            ),
            Article(
                title="Short Article",
                url="https://example.com/short",
                content="Too short",  # Below minimum length
                published_date=None,
            ),
        ]

    async def test_full_pipeline_integration(self, profile, sample_raw_articles):
        """Test complete pipeline: validate → normalize → quality → topics → relevance."""
        # Initialize activities with real dependencies
        activities = ProcessingActivities()

        # Phase 1: Validation
        validation_result = await activities.validate_and_filter_batch(
            sc.BatchValidationRequest(articles=sample_raw_articles)
        )
        assert validation_result.valid_count == 1  # Only first article valid
        assert validation_result.invalid_count == 2  # Spam + short

        # Get valid articles only
        valid_articles = [
            article
            for article in sample_raw_articles
            if validation_result.validation_results[str(article.url)].is_valid
        ]
        assert len(valid_articles) == 1

        # Phase 2: Normalization
        normalize_result = await activities.normalize_articles_batch(
            sc.BatchNormalizationRequest(articles=valid_articles)
        )
        assert normalize_result.total_processed == 1
        normalized_articles = normalize_result.articles

        # Phase 3: Quality Scoring
        quality_result = await activities.score_quality_batch(
            sc.BatchQualityRequest(articles=normalized_articles)
        )
        assert quality_result.total_scored == 1
        quality_scores = {url: result.quality_score for url, result in quality_result.quality_results.items()}

        # Phase 4: Topic Extraction
        topics_result = await activities.extract_topics_batch(
            sc.BatchTopicExtractionRequest(articles=normalized_articles)
        )
        assert topics_result.total_processed == 1
        assert topics_result.articles_with_topics >= 0  # May or may not find topics

        # Phase 5: Relevance Scoring
        relevance_result = await activities.score_relevance_batch(
            sc.BatchRelevanceRequest(
                profile_id=str(profile.id),
                articles=topics_result.articles,
                quality_scores=quality_scores,
            )
        )
        assert relevance_result.total_scored == 1

        # Verify final result
        final_article_url = str(valid_articles[0].url)
        relevance = relevance_result.relevance_results[final_article_url]

        # Should be relevant (contains "Python", "AI" keywords)
        assert relevance.relevance_score > 0
        assert relevance.breakdown.keyword_match_score > 0

    async def test_cache_warm_integration(self, profile, sample_raw_articles):
        """Test full pipeline twice - verify cache effectiveness."""
        activities = ProcessingActivities()
        valid_article = sample_raw_articles[0]  # Use only valid article

        # First run: cold cache
        validation_result1 = await activities.validate_and_filter_batch(
            sc.BatchValidationRequest(articles=[valid_article])
        )
        quality_result1 = await activities.score_quality_batch(
            sc.BatchQualityRequest(articles=[valid_article])
        )
        topics_result1 = await activities.extract_topics_batch(
            sc.BatchTopicExtractionRequest(articles=[valid_article])
        )
        relevance_result1 = await activities.score_relevance_batch(
            sc.BatchRelevanceRequest(
                profile_id=str(profile.id),
                articles=[valid_article],
            )
        )

        # Track first run AI calls
        first_run_ai_calls = (
            validation_result1.ai_calls
            + quality_result1.ai_calls
            + topics_result1.ai_calls
            + relevance_result1.ai_calls
        )

        # Second run: warm cache
        validation_result2 = await activities.validate_and_filter_batch(
            sc.BatchValidationRequest(articles=[valid_article])
        )
        quality_result2 = await activities.score_quality_batch(
            sc.BatchQualityRequest(articles=[valid_article])
        )
        topics_result2 = await activities.extract_topics_batch(
            sc.BatchTopicExtractionRequest(articles=[valid_article])
        )
        relevance_result2 = await activities.score_relevance_batch(
            sc.BatchRelevanceRequest(
                profile_id=str(profile.id),
                articles=[valid_article],
            )
        )

        # Track second run AI calls
        second_run_ai_calls = (
            validation_result2.ai_calls
            + quality_result2.ai_calls
            + topics_result2.ai_calls
            + relevance_result2.ai_calls
        )

        # Verify cache effectiveness
        assert first_run_ai_calls > 0, "First run should make AI calls"
        assert second_run_ai_calls == 0, "Second run should use cache only"

        # Verify results identical
        assert (
            quality_result1.quality_results[str(valid_article.url)].quality_score
            == quality_result2.quality_results[str(valid_article.url)].quality_score
        )
```

---

## Mocking Best Practices

### 1. Use pytest-mock for cleaner mocks

```python
def test_example(mocker):
    """Use mocker fixture instead of patch context managers."""
    mock_redis = mocker.patch("app.temporal.activities.processing.get_redis_client")
    mock_redis.return_value.get = AsyncMock(return_value=None)
```

### 2. Create reusable fixtures

```python
# conftest.py
@pytest.fixture
def mock_redis_empty_cache():
    """Redis client with empty cache."""
    client = AsyncMock()
    client.get.return_value = None
    client.setex.return_value = True
    return client

@pytest.fixture
def mock_redis_populated_cache(sample_cached_data):
    """Redis client with populated cache."""
    client = AsyncMock()
    client.get.return_value = sample_cached_data.encode()
    return client
```

### 3. Use side_effect for complex scenarios

```python
def test_mixed_cache_hits_and_misses(mock_redis):
    """Test scenario with some cache hits and some misses."""
    mock_redis.get.side_effect = [
        b'{"cached": "data1"}',  # First call: cache hit
        None,                     # Second call: cache miss
        b'{"cached": "data3"}',  # Third call: cache hit
    ]
```

---

## Running Tests

### Unit tests only (fast, no Docker)

```bash
uv run pytest -m unit
```

### Integration tests (requires Docker)

```bash
# Start Docker services
docker-compose up -d postgres redis temporal

# Run integration tests
uv run pytest -m integration
```

### Coverage report

```bash
uv run pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Run specific test file

```bash
uv run pytest tests/test_temporal/test_activities_validation.py -v
```

---

## Next Steps

1. Start with Phase 1.1: Create `test_activities_validation.py`
2. Copy the example tests and adapt fixtures
3. Run tests: `uv run pytest tests/test_temporal/test_activities_validation.py -v`
4. Check coverage: `uv run pytest tests/test_temporal/test_activities_validation.py --cov=app/temporal/activities/processing`
5. Iterate until all tests pass and coverage targets met

---

**Last Updated**: 2025-11-05
