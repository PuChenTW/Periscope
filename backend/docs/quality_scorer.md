# Content Quality Scoring Module

## Overview

The Content Quality Scoring module provides hybrid quality assessment for articles by combining rule-based metadata scoring with AI-powered content quality analysis. This produces a final quality score (0-100 scale) used for article ranking, filtering, and prioritization in the content pipeline.

**Location:** `app/processors/quality_scorer.py`

**Status:** ✅ Implemented (Decoupled from ContentNormalizer)

**Pipeline Position:**
```
RSS Fetcher → ContentNormalizer → QualityScorer → TopicExtractor → SimilarityDetector → Summarizer → Digest
```

## Implementation Status

### ✅ Completed Features
- **Hybrid Quality Scoring**: Rule-based metadata scoring + AI-powered content assessment (0-100 scale)
- **Rule-Based Metadata Scoring**: Objective completeness metrics (0-50 points)
- **AI-Powered Content Quality**: Subjective quality assessment using PydanticAI (0-50 points)
- **AI Provider Integration**: Uses configurable AI provider abstraction (Gemini/OpenAI)
- **Async Architecture**: Full async/await support for AI integration
- **Dependency Injection**: Constructor-based configuration and AI provider injection
- **Graceful Degradation**: Falls back to metadata-only scoring when AI disabled
- **Comprehensive Testing**: 4 tests covering all scoring scenarios

## Key Features & Usage

### 1. Hybrid Quality Scoring

**Purpose:** Ranks articles by combining objective metadata completeness with subjective content quality

**Implementation:** Two-component hybrid scoring system

#### Rule-Based Component (0-50 points)
**Metadata Completeness Scoring:**
- Has author: +10 points
- Has published_at: +10 points
- Has tags (1+): +5 points
- Content length > 500 chars: +15 points
- Content length > 1000 chars: +10 points (bonus)

#### AI-Powered Component (0-50 points)
**Content Quality Assessment using PydanticAI:**

```python
class ContentQualityResult(BaseModel):
    writing_quality: int      # 0-20 points
    informativeness: int      # 0-20 points
    credibility: int          # 0-10 points
    reasoning: str
```

**Assessment Criteria:**
- **Writing Quality (0-20)**: Clarity, coherence, grammar, structure, readability
- **Informativeness (0-20)**: Depth, coverage, value, insights, specific details
- **Credibility (0-10)**: Evidence, balanced perspective, professional tone

**Final Score:** metadata_score + ai_content_score = 0-100 points

**Configuration:**
- `quality_scoring_enabled`: Toggle AI quality assessment (default: True)
- When disabled, metadata score is scaled to 0-100 range

**Why Hybrid Approach:**
- Fast rule-based metrics for objective completeness
- Deep AI analysis for subjective content quality
- Balanced scoring resistant to manipulation
- Graceful degradation when AI unavailable

**Storage:**
Scores stored in `article.metadata`:
```python
{
    "quality_score": 64,
    "quality_breakdown": {
        "metadata_score": 25,
        "ai_content_score": 39
    }
}
```

**Example:**
```python
# Complete article: author ✓, date ✓, tags ✓, >1000 chars, high AI quality
# Metadata: 10 + 10 + 5 + 15 + 10 = 50 points
# AI: writing(18) + info(17) + cred(9) = 44 points
# Total: 94/100

# Minimal article: no metadata, basic content
# Metadata: 0 points (scaled to 0 when AI disabled)
# AI: writing(10) + info(10) + cred(5) = 25 points (or 0 if disabled)
# Total: 0-25/100
```

**Why needed:**
- Prioritize high-quality articles when feed has >100 items
- More accurate than metadata-only scoring
- Fallback to rule-based when AI processing fails
- Enables future "digest preview" features

## Implementation Design

### QualityScorer Class

**Constructor:**
```python
def __init__(
    self,
    quality_scoring_enabled: bool = True,
    ai_provider: AIProvider | None = None,
)
```

**Pydantic Models:**
```python
class ContentQualityResult(BaseModel):
    writing_quality: int      # 0-20
    informativeness: int      # 0-20
    credibility: int          # 0-10
    reasoning: str
```

**Main Methods:**
```python
# Public API
async def calculate_quality_score(self, article: Article) -> Article

# Internal methods
def _calculate_metadata_score(self, article: Article) -> int
async def _assess_content_quality(self, article: Article) -> ContentQualityResult
```

**Key Implementation Details:**
- ✅ **Single AI Agent** - `quality_agent` for content quality assessment
- ✅ **Async methods** - Required for AI provider integration
- ✅ **Parameter-based config** - Accepts specific parameters instead of Settings object
- ✅ **AI provider injection** - Uses AIProvider abstraction for quality assessment
- ✅ **Structured outputs** - Pydantic models for AI results with validation

**Key Design Principles:**
- **Async/Await:** Required for AI provider integration
- **Input:** Article → **Output:** Article (with quality_score in metadata)
- **Never raises exceptions:** Uses fallbacks and logs warnings
- **Dependency Injection:** AI provider can be injected for testing
- **Idempotent:** Running twice produces same result
- **Graceful Degradation:** Returns neutral scores on AI errors
- **Uses textwrap.dedent():** For clean prompts (see CLAUDE.md coding guidelines)

## Configuration Settings

**Location:** `app/config.py`

**Current Settings:**

```python
# Content Quality Scoring Settings
quality_scoring_enabled: bool = Field(True, env="QUALITY_SCORING_ENABLED")
```

**Environment Variables:**
```bash
QUALITY_SCORING_ENABLED=true        # Enable AI-powered quality assessment
```

## Test Suite

**Location:** `tests/test_processors/test_quality_scorer.py`

**Current Status:** ✅ 4 tests implemented and passing

### Implemented Test Scenarios

1. ✅ **Metadata Score Calculation** - Rule-based scoring works correctly
2. ✅ **Metadata Score Minimal** - Minimal articles scored appropriately
3. ✅ **Hybrid Quality Scoring Enabled** - Combined metadata + AI scoring
4. ✅ **Quality Scoring Disabled** - AI scoring can be disabled

### Test Structure

Tests use **async/await** pattern with mock AI provider for deterministic testing:

```python
@pytest.fixture
def mock_ai_provider(self):
    """Create a mock AI provider for testing."""
    mock_provider = MagicMock()

    def create_agent_mock(output_type, system_prompt):
        if output_type == ContentQualityResult:
            test_model = TestModel(
                custom_output_args=ContentQualityResult(
                    writing_quality=15,
                    informativeness=16,
                    credibility=8,
                    reasoning="Good quality article"
                )
            )
        return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

    mock_provider.create_agent = create_agent_mock
    return mock_provider

@pytest.mark.asyncio
async def test_hybrid_quality_scoring_enabled(self, quality_scorer):
    """Test hybrid quality scoring with AI enabled."""
    # Uses TestModel from pydantic_ai for deterministic AI responses
    result = await quality_scorer.calculate_quality_score(article)
    assert result.metadata["quality_score"] == 64
```

## Integration with Content Pipeline

### Usage in Processing Pipeline

```python
from app.config import get_settings
from app.processors.fetchers.factory import create_fetcher
from app.processors.normalizer import ContentNormalizer
from app.processors.quality_scorer import QualityScorer
from app.processors.topic_extractor import TopicExtractor
from app.processors.similarity_detector import SimilarityDetector

async def process_content(source_url: str):
    settings = get_settings()

    # Step 1: Fetch content
    fetcher = create_fetcher(source_url)
    fetch_result = await fetcher.fetch_content(source_url)

    # Step 2: Normalize articles (spam detection, metadata standardization)
    normalizer = ContentNormalizer(
        content_min_length=settings.content_min_length,
        content_max_length=settings.content_max_length,
        spam_detection_enabled=settings.spam_detection_enabled,
        title_max_length=settings.title_max_length,
        author_max_length=settings.author_max_length,
        tag_max_length=settings.tag_max_length,
        max_tags_per_article=settings.max_tags_per_article,
    )

    normalized_articles = []
    for article in fetch_result.articles:
        normalized = await normalizer.normalize(article)  # Note: async
        if normalized:  # None if rejected
            normalized_articles.append(normalized)

    logger.info(f"Normalized {len(normalized_articles)}/{len(fetch_result.articles)} articles")

    # Step 3: Calculate quality scores
    quality_scorer = QualityScorer(
        quality_scoring_enabled=settings.quality_scoring_enabled,
    )

    scored_articles = []
    for article in normalized_articles:
        scored = await quality_scorer.calculate_quality_score(article)
        scored_articles.append(scored)

    logger.info(f"Scored {len(scored_articles)} articles")

    # Step 4: Extract topics
    topic_extractor = TopicExtractor()
    for article in scored_articles:
        article.ai_topics = await topic_extractor.extract_topics(article)

    # Step 5: Detect similarity and group
    similarity_detector = SimilarityDetector()
    article_groups = await similarity_detector.detect_similar_articles(scored_articles)

    return article_groups
```

### Error Handling

The quality scorer uses a **graceful degradation** strategy:

- **AI scoring disabled:** Falls back to metadata-only scoring (scaled to 0-100)
- **AI assessment errors:** Returns neutral scores (writing=10, info=10, cred=5)
- **Unexpected errors:** Catches and logs, returns neutral scores

This ensures the pipeline continues processing even with AI failures.

## Separation of Concerns

### Why Decoupled from ContentNormalizer?

The quality scoring functionality was originally part of ContentNormalizer but was extracted into a separate module to:

1. **Single Responsibility Principle**: Each class has one clear purpose
   - `ContentNormalizer`: Data validation and metadata standardization
   - `QualityScorer`: Article quality assessment

2. **Testability**: Quality scoring can be tested independently

3. **Reusability**: Quality scores can be calculated at any pipeline stage

4. **Flexibility**: Easy to swap quality scoring algorithms

5. **Maintainability**: Changes to quality scoring don't affect normalization

### Related Modules

- **ContentNormalizer** (`app/processors/normalizer.py`): Handles data validation, spam detection, and metadata standardization
- **TopicExtractor** (`app/processors/topic_extractor.py`): Extracts key topics from articles
- **SimilarityDetector** (`app/processors/similarity_detector.py`): Groups similar articles

## Success Criteria

### ✅ Achieved

- ✅ QualityScorer processes articles consistently
- ✅ All edge cases handled gracefully with fallbacks
- ✅ Test coverage: 4 comprehensive tests passing
- ✅ No exceptions raised during scoring (graceful degradation)
- ✅ Integration-ready for content processing pipeline
- ✅ Hybrid scoring accurately reflects article completeness and content quality
- ✅ Async architecture supports AI integration
- ✅ Logging provides visibility into scoring results

## Future Enhancements

- **Advanced quality metrics:** Additional scoring dimensions (timeliness, originality, etc.)
- **Enhanced AI models:** Deeper content analysis with more sophisticated models
- **Performance optimization:** Batch AI processing, caching strategies
- **Quality trends:** Track quality scores over time for sources
- **Custom scoring weights:** User-configurable importance of different quality factors
