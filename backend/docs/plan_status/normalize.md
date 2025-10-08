# Content Normalization Module

## Overview

The Content Normalization module standardizes article structure and metadata beyond what the RSS fetcher provides. It ensures consistent data quality before AI processing by validating, cleaning, and enriching article data.

**Location:** `app/processors/normalizer.py`

**Status:** ✅ Phase 2 Complete (Content Validation and Metadata Standardization)

**Pipeline Position:**
```
RSS Fetcher → ContentNormalizer → QualityScorer → TopicExtractor → SimilarityDetector → Summarizer → Digest
```

## Implementation Status

### ✅ Completed Features (Phase 1 & 2)
- **AI-Powered Spam Detection**: Uses PydanticAI with configurable providers (Gemini/OpenAI)
- **Content Validation**: Empty content check, minimum/maximum length enforcement
- **Metadata Standardization**: Author normalization, tag deduplication, title validation, URL cleaning
- **Content Management**: Smart truncation at word boundaries, tracking parameter removal
- **Async Architecture**: Full async/await support for AI integration
- **Dependency Injection**: Constructor-based configuration and AI provider injection
- **Comprehensive Testing**: 22 tests covering validation and normalization

### 📋 Planned Features (Future Phases)
- Date handling (fallback to fetch_timestamp)
- Language detection and filtering

## Why Normalization is Needed

The RSS fetcher handles **format-level parsing**:
- HTML tag removal
- HTML entity decoding
- Whitespace normalization

The normalizer adds **business-level validation and enrichment**:
- AI-powered spam and low-quality content filtering
- Content length validation
- Future: Cross-field validation, metadata standardization, quality scoring

**Separation of Concerns:** Fetcher = parse RSS format → Normalizer = enforce business rules

## Key Features & Usage

### 1. Content Validation ✅ (IMPLEMENTED)

**Purpose:** Filters out low-quality or spam articles using AI-powered analysis

**Implementation:**
- **Empty Content Check**: Rejects articles with None, empty, or whitespace-only content
- **Minimum Length Validation**: Configurable threshold (default: 100 chars) to filter stub articles
- **AI-Powered Spam Detection**: Uses PydanticAI agents to analyze content semantics and identify spam

**AI Spam Detection Details:**

The normalizer uses a structured AI agent that returns:
```python
class SpamDetectionResult(BaseModel):
    is_spam: bool              # Whether content is spam
    confidence: float          # Confidence score (0.0-1.0)
    reasoning: str             # Explanation of determination
```

**Spam Indicators Detected:**
- Excessive promotional language or calls to action
- Repeated characters, words, or phrases
- Misleading clickbait with no substance
- Excessive capitalization or punctuation
- Obvious advertising or marketing content
- Low-quality automated or bot-generated content
- Scam or fraudulent content patterns

**Legitimate Content Preserved:**
- News articles with some promotional elements
- Product announcements from legitimate companies
- Educational or informational content
- Opinion pieces or blog posts

**Why AI-Powered Detection:**
- More accurate than heuristic pattern matching
- Understands context and semantics
- Adapts to evolving spam techniques
- Reduces false positives compared to rule-based systems

**Example:**
```python
# Input: Article with "Read more..." (18 chars)
# Output: Rejected (content too short)

# Input: "BUY NOW!!! AMAZING DEAL!!! Click here for LIMITED TIME!!!" repeated
# Output: Rejected (AI detects spam with 0.95 confidence)

# Input: "Apple announces new iPhone 16 with advanced features. Available for $999..."
# Output: Accepted (AI recognizes legitimate product announcement)
```

**Configuration:**
- `content_min_length`: Minimum content length in characters (default: 100)
- `spam_detection_enabled`: Toggle AI spam detection on/off (default: True)

### 2. Metadata Standardization ✅ (IMPLEMENTED)

#### Author Name Normalization

**Purpose:** Ensures consistent author representation

**Features:**
- **Title case conversion:** "john doe" → "John Doe"
- **Max length enforcement (100 chars):** Truncates overly long author fields
- **Whitespace cleanup:** Removes extra spaces, tabs, newlines

**Why needed:**
- Consistent display in digests
- Database storage optimization
- Handles malformed RSS feeds

**Example:**
```python
# Input: "  john   DOE  "
# Output: "John Doe"

# Input: "John Doe (Senior Tech Correspondent for Global News Network covering AI and Machine Learning Topics)"
# Output: "John Doe (Senior Tech Correspondent For Global News Network Covering Ai And Machine Learning T..."
```

#### Tag Deduplication & Standardization

**Purpose:** Cleans up messy tag data from feeds

**Features:**
- **Lowercase normalization:** "AI", "ai", "Ai" → all become "ai"
- **Deduplication:** Removes duplicate tags after normalization
- **Max tag length (50 chars):** Prevents extremely long tags
- **Max tags per article (20):** Limits tag bloat

**Why needed:**
- Improves topic extraction accuracy
- Reduces noise in similarity detection
- Consistent categorization across sources

**Example:**
```python
# Input: ["AI", "Machine Learning", "ai", "ML", "machine learning"]
# Output: ["ai", "machine learning", "ml"]

# Input: 35 tags
# Output: First 20 tags (after deduplication and normalization)
```

### 3. Date Handling 📋 (PLANNED)

**Purpose:** Ensures every article has a valid timestamp

**Features:**
- **Missing date fallback:** Uses fetch_timestamp if published_at is None
- **Timezone normalization:** Convert to UTC

**Why needed:**
- Required for time-based filtering ("last 24 hours")
- Chronological ordering in digests
- Prevents null date errors in downstream processing

**Example:**
```python
# Input: Article with published_at=None
# Output: Article with published_at=fetch_timestamp (e.g., 2024-01-15 10:00:00 UTC)
```

### 4. Content Length Enforcement ✅ (IMPLEMENTED)

**Purpose:** Manages token limits and processing costs

**Features:**
- **Max content length (50,000 chars):** Truncates extremely long articles
- **Smart truncation:** Cuts at word boundaries to avoid broken sentences
- **Content preview preservation:** Keeps first N characters for processing

**Why needed:**
- Prevents AI timeout errors
- Controls API costs
- Handles edge cases like full-text RSS feeds or scraped content

**Example:**
```python
# Input: Article with 75,000 characters of content
# Output: Article with 50,000 characters, truncated at last complete word
```

### 5. URL Normalization ✅ (IMPLEMENTED)

**Purpose:** Cleans article URLs for deduplication

**Features:**
- **Remove tracking parameters:** `?utm_source=...`, `?ref=...`, `?campaign=...`
- **Scheme normalization:** Ensure https:// consistency
- **Trailing slash normalization:** Remove or add consistently

**Why needed:**
- Prevents duplicate articles with different tracking params
- Cleaner links in email digests
- Improves deduplication accuracy

**Example:**
```python
# Input: "https://example.com/article?utm_source=rss&utm_campaign=feed&ref=twitter"
# Output: "https://example.com/article"

# Input: "http://example.com/article"
# Output: "https://example.com/article"
```

### 6. Language Detection 📋 (PLANNED)

**Purpose:** Flags non-English content (Phase 1 supports English only)

**Features:**
- **Detection:** Uses simple heuristics or langdetect library
- **Action:** Logs warning but doesn't reject (for future multi-language support)
- **Language field:** Adds detected_language to metadata

**Why needed:**
- Helps identify feed configuration issues
- Prepares for future language filtering
- Provides visibility into content language distribution

**Example:**
```python
# Input: Article in Spanish
# Output: Article with metadata["detected_language"] = "es" + warning logged
```

### 7. Title Validation ✅ (IMPLEMENTED)

**Purpose:** Ensures every article has a usable title

**Features:**
- **Existence check:** Reject articles without titles (can't be displayed)
- **Whitespace cleanup:** Removes extra spaces, tabs, newlines
- **Max length (500 chars):** Truncates extremely long titles
- **Fallback:** Uses "Untitled Article" if title is empty after cleanup

**Why needed:**
- Titles are required for email display
- Prevents broken digest layouts
- Handles malformed feeds gracefully

**Example:**
```python
# Input: "   Breaking News:    New AI Model Released   "
# Output: "Breaking News: New AI Model Released"

# Input: Title with 700 characters
# Output: Title truncated to 500 characters at last complete word
```

## Implementation Design

### ContentNormalizer Class

**Constructor:**
```python
def __init__(
    self,
    content_min_length: int = 100,
    content_max_length: int = 50000,
    spam_detection_enabled: bool = True,
    title_max_length: int = 500,
    author_max_length: int = 100,
    tag_max_length: int = 50,
    max_tags_per_article: int = 20,
    ai_provider: AIProvider | None = None,
)
```

**Pydantic Models:**
```python
class SpamDetectionResult(BaseModel):
    is_spam: bool
    confidence: float
    reasoning: str
```

**Main Methods:**
```python
# Phase 1: Content Validation
async def normalize(self, article: Article) -> Article | None
async def _validate_content(self, article: Article) -> bool
async def _detect_spam(self, article: Article) -> bool

# Phase 2: Metadata Standardization
def _normalize_title(self, article: Article) -> Article
def _normalize_author(self, article: Article) -> Article
def _normalize_tags(self, article: Article) -> Article
def _normalize_url(self, article: Article) -> Article
def _enforce_content_length(self, article: Article) -> Article
```

**Key Implementation Details:**
- ✅ **Single AI Agent** - `spam_agent` for spam detection
- ✅ **Async methods** - Required for AI provider integration
- ✅ **Parameter-based config** - No longer stores Settings object, accepts specific parameters
- ✅ **AI provider injection** - Uses AIProvider abstraction for spam detection
- ✅ **Structured outputs** - Pydantic models for AI results with validation

**Key Design Principles:**
- **Async/Await:** Required for AI provider integration
- **Input:** Article → **Output:** Article (normalized) or None (rejected)
- **Never raises exceptions:** Uses fallbacks and logs warnings
- **Dependency Injection:** AI provider can be injected for testing
- **Idempotent:** Running twice produces same result
- **Graceful Degradation:** Returns False (not spam) on AI errors
- **Uses textwrap.dedent():** For clean prompts (see CLAUDE.md coding guidelines)

## Configuration Settings

**Location:** `app/config.py`

**Current Settings (Phase 1 & 2):**

```python
# Content Normalization Settings
content_min_length: int = Field(100, env="CONTENT_MIN_LENGTH")
content_max_length: int = Field(50000, env="CONTENT_MAX_LENGTH")
spam_detection_enabled: bool = Field(True, env="SPAM_DETECTION_ENABLED")
title_max_length: int = Field(500, env="TITLE_MAX_LENGTH")
author_max_length: int = Field(100, env="AUTHOR_MAX_LENGTH")
tag_max_length: int = Field(50, env="TAG_MAX_LENGTH")
max_tags_per_article: int = Field(20, env="MAX_TAGS_PER_ARTICLE")
```

**Environment Variables:**
```bash
CONTENT_MIN_LENGTH=100              # Minimum content length to accept
CONTENT_MAX_LENGTH=50000            # Maximum content length (truncates beyond)
SPAM_DETECTION_ENABLED=true         # Enable AI-powered spam detection
TITLE_MAX_LENGTH=500                # Maximum title length
AUTHOR_MAX_LENGTH=100               # Maximum author name length
TAG_MAX_LENGTH=50                   # Maximum individual tag length
MAX_TAGS_PER_ARTICLE=20             # Maximum tags per article
```

## Test Suite

**Location:** `tests/test_processors/test_normalizer.py`

**Current Status:** ✅ 22 tests implemented and passing

### Implemented Test Scenarios (Phase 1 & 2)

**Phase 1 - Content Validation (11 tests):**
1. ✅ **Valid Article Normalization** - Complete article passes validation
2. ✅ **Empty Content Rejection** - Articles with empty/None content are rejected
3. ✅ **Whitespace-Only Content** - Whitespace-only content is rejected
4. ✅ **Content Too Short** - Below minimum length is rejected
5. ✅ **Content Exactly Minimum Length** - Exactly minimum chars passes
6. ✅ **Unicode Content** - Unicode characters handled correctly
7. ✅ **Emoji Content** - Emojis in content handled properly
8. ✅ **AI Spam Detection Enabled** - Spam content detected and rejected
9. ✅ **Spam Detection Disabled** - Can disable spam detection via parameter
10. ✅ **Minimal Metadata** - Articles with only required fields accepted
11. ✅ **Field Preservation** - Article fields preserved during normalization

**Phase 2 - Metadata Normalization (11 tests):**
12. ✅ **Title Whitespace Cleanup** - Multiple spaces and newlines normalized
13. ✅ **Title Truncation** - Long titles truncated at word boundaries
14. ✅ **Title Empty Fallback** - Empty titles get "Untitled Article" fallback
15. ✅ **Author Title Case** - Author names converted to title case
16. ✅ **Author Truncation** - Long author names truncated properly
17. ✅ **Tag Deduplication** - Duplicate tags removed after normalization
18. ✅ **Tag Max Limit** - Articles limited to max tags per article
19. ✅ **Tag Length Limit** - Individual tags truncated to max length
20. ✅ **URL Tracking Params Removal** - utm_* and ref params removed
21. ✅ **URL HTTPS Upgrade** - http:// URLs upgraded to https://
22. ✅ **Content Length Truncation** - Long content truncated at word boundaries

### Planned Test Scenarios (Future Phases)

- **Date Handling** - Missing date fallback to fetch_timestamp
- **Language Detection** - Non-English content detection and logging

### Test Structure

Tests use **async/await** pattern with mock AI provider for deterministic testing:

```python
@pytest.fixture
def mock_ai_provider(self):
    """Create a mock AI provider for testing."""
    mock_provider = MagicMock()

    def create_agent_mock(output_type, system_prompt):
        if output_type == SpamDetectionResult:
            test_model = TestModel(
                custom_output_args=SpamDetectionResult(
                    is_spam=False, confidence=0.9, reasoning="Valid article"
                )
            )
        else:
            test_model = TestModel()
        return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

    mock_provider.create_agent = create_agent_mock
    return mock_provider

@pytest.mark.asyncio
async def test_normalize_valid_article(self, normalizer):
    """Test normalization with AI spam detection."""
    # Uses TestModel from pydantic_ai for deterministic AI responses
    result = await normalizer.normalize(article)
    assert result is not None
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

    # Step 2: Normalize articles (with AI spam detection)
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

The normalizer uses a **graceful degradation** strategy:

- **Low-quality content:** Returns None (rejected)
- **Malformed metadata:** Applies fallbacks (e.g., "Unknown Author")
- **Validation failures:** Logs warnings but doesn't crash
- **Unexpected errors:** Catches and logs, returns original article

This ensures the pipeline continues processing even with problematic articles.

## Implementation Checklist

### Phase 1 - Content Validation ✅ COMPLETED

- ✅ Create `app/processors/normalizer.py` with ContentNormalizer class
- ✅ Implement async architecture with AI provider integration
- ✅ Implement content validation:
  - ✅ Empty content check
  - ✅ Minimum length validation
  - ✅ AI-powered spam detection with SpamDetectionResult
- ✅ Add configuration settings to `app/config.py`:
  - ✅ content_min_length
  - ✅ spam_detection_enabled
- ✅ Create comprehensive test suite (13 tests):
  - ✅ Valid article normalization
  - ✅ Empty/whitespace content rejection
  - ✅ Content length validation (too short, exactly min, just below)
  - ✅ Unicode and emoji handling
  - ✅ Custom configuration parameters
  - ✅ AI spam detection enabled/disabled
  - ✅ Minimal metadata handling
  - ✅ Field preservation
- ✅ All tests passing (13/13)
- ✅ Integration with AI provider abstraction

### Phase 2 - Metadata & Content Management ✅ COMPLETED

- ✅ Implement metadata standardization:
  - ✅ Author normalization (title case, length limits)
  - ✅ Tag deduplication and normalization
  - ✅ Title validation and cleanup
- ✅ Implement content management:
  - ✅ Content length enforcement (max 50,000 chars)
  - ✅ Smart truncation at word boundaries
  - ✅ URL normalization (tracking params, scheme)
- ✅ Add configuration settings (7 total)
- ✅ Test suite with 22 comprehensive tests
- ✅ All tests passing (22/22)

### Phase 3 - Future Enhancements 📋 PLANNED

- [ ] Date handling (fallback to fetch_timestamp)
- [ ] Language detection and filtering
- [ ] Integration test with full pipeline (RSS → Normalize → Topic → Similarity)

## Success Criteria

### Phase 1 (Content Validation) ✅ ACHIEVED

- ✅ ContentNormalizer processes articles consistently
- ✅ All edge cases handled gracefully with fallbacks
- ✅ Test coverage: 13 comprehensive tests passing
- ✅ No exceptions raised during normalization (graceful degradation)
- ✅ Integration-ready for content processing pipeline
- ✅ AI-powered spam detection with confidence scoring
- ✅ Logging provides visibility into rejection reasons
- ✅ Async architecture supports AI integration

### Phase 2 (Metadata & Content Management) ✅ ACHIEVED

- ✅ Metadata standardization complete (title, author, tags, URL)
- ✅ Content management implemented (max length, smart truncation)
- ✅ Test coverage: 22 comprehensive tests
- ✅ All Phase 2 features implemented and tested
- ✅ Clean separation of concerns (normalization vs quality scoring)

### Phase 3 (Future) 📋 PENDING

- [ ] Date handling with fetch_timestamp fallback
- [ ] Language detection and filtering
- [ ] Performance optimization: <1ms per article normalization (excluding AI calls)
- [ ] Full pipeline integration test

## Future Enhancements

- **Multi-language support:** Full language detection and filtering
- **Advanced spam detection:** Enhanced ML-based spam classification with evolving patterns
- **Content summarization preview:** Generate preview snippets for digest previews
- **Media extraction:** Extract and validate images, videos from content
- **Duplicate detection:** Hash-based deduplication before AI processing
- **Performance optimization:** Batch AI processing, caching strategies

## Related Documentation

- **Quality Scoring**: See `docs/quality_scorer.md` for hybrid quality assessment (decoupled from normalizer)
- **Topic Extraction**: See `docs/topic_extractor.md` for AI-powered topic identification
- **Similarity Detection**: See `docs/similarity_detector.md` for article grouping
