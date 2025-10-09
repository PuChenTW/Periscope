# Article Summarization Module

## Overview

The Article Summarization module provides AI-powered article summarization to generate concise, user-friendly summaries for the daily digest. It supports multiple summary styles (brief, detailed, bullet points) and integrates seamlessly with the content processing pipeline.

**Location:** `app/processors/summarizer.py`

**Status:** ✅ Implemented and Tested

**Pipeline Position:**
```
RSS Fetcher → Normalizer → QualityScorer → TopicExtractor → Summarizer → SimilarityDetector → Digest
```

## Implementation Status

### ✅ Completed Features
- **AI-Powered Summarization**: Uses PydanticAI with configurable AI providers (Gemini/OpenAI)
- **Multiple Summary Styles**: Brief, detailed, and bullet points formats
- **Configurable Length Limits**: Customizable max word count per summary
- **Content Truncation**: Efficient token usage with configurable content length
- **Graceful Degradation**: Fallback to content excerpts on AI errors
- **Topic Integration**: Uses topics from TopicExtractor for enhanced context
- **Async Architecture**: Full async/await support for AI integration
- **Dependency Injection**: Constructor-based configuration and AI provider injection
- **Comprehensive Testing**: 18 tests covering all scenarios

## Key Features & Usage

### 1. Summary Styles

The summarizer supports three different summary styles based on user preferences:

#### Brief Style (Default)
**Purpose:** Quick overview for busy readers

**Characteristics:**
- 1-2 paragraphs
- Focuses on core message
- Simple, clear sentences
- Max length: configurable (default: 500 words)

**Use Case:** Daily digest for users who want quick updates

#### Detailed Style
**Purpose:** Comprehensive understanding

**Characteristics:**
- 3-4 paragraphs
- Includes important context and background
- Covers multiple aspects of the topic
- Explains technical terms when needed
- Max length: configurable (default: 500 words)

**Use Case:** Users who want deeper insights

#### Bullet Points Style
**Purpose:** Scannable key information

**Characteristics:**
- List of key points
- Each point is self-contained
- Concise, action-oriented language
- Organized by importance
- Max length: configurable (default: 500 words total)

**Use Case:** Users who prefer structured, scannable summaries

### 2. AI-Powered Summarization

**Implementation:** Uses PydanticAI with configurable providers

```python
class SummaryResult(BaseModel):
    summary: str                 # Concise summary of article content
    key_points: list[str]       # 3-5 key points or takeaways
    reasoning: str              # Explanation of summarization approach
```

**Process:**
1. Article content is truncated to configurable length (default: 2000 chars)
2. Context includes title, tags, and AI-extracted topics
3. AI generates structured summary based on style
4. Summary is formatted according to style preferences
5. Result is stored in article.summary field

**Example:**
```python
from app.processors.summarizer import Summarizer

# Create summarizer with brief style
summarizer = Summarizer(summary_style="brief")

# Generate summary
article_with_summary = await summarizer.summarize(article)

# Access summary
print(article_with_summary.summary)
```

### 3. Fallback Strategies

The summarizer uses multiple fallback strategies to ensure robustness:

**Minimal Content Handling:**
- Articles with <100 characters: Use first 150 chars as excerpt
- Empty content: Use article title as fallback

**AI Error Handling:**
- AI service failures: Use first 300 chars of content
- Timeout errors: Graceful fallback to excerpt
- Never raises exceptions - always returns article with summary

**Example:**
```python
# Minimal content - no AI call needed
short_article = Article(title="News", content="Brief update.", ...)
result = await summarizer.summarize(short_article)
# result.summary = "Brief update."

# AI error - fallback to excerpt
with ai_service_down:
    result = await summarizer.summarize(long_article)
    # result.summary = first_300_chars + "..."
```

### 4. Integration with Content Pipeline

The summarizer integrates with other processors for enhanced results:

**Topic Extractor Integration:**
- Uses `article.ai_topics` for additional context
- Topics inform summarization focus
- Improves relevance and accuracy

**Quality Scorer Integration:**
- Can prioritize high-quality articles for summarization
- Quality scores can influence summary style selection

**Usage in Pipeline:**
```python
from app.config import get_settings
from app.processors.fetchers.factory import create_fetcher
from app.processors.normalizer import ContentNormalizer
from app.processors.quality_scorer import QualityScorer
from app.processors.topic_extractor import TopicExtractor
from app.processors.summarizer import Summarizer
from app.processors.similarity_detector import SimilarityDetector

async def process_content(source_url: str, summary_style: str = "brief"):
    settings = get_settings()

    # Step 1: Fetch content
    fetcher = create_fetcher(source_url)
    fetch_result = await fetcher.fetch_content(source_url)

    # Step 2: Normalize articles
    normalizer = ContentNormalizer(
        content_min_length=settings.content_min_length,
        content_max_length=settings.content_max_length,
        spam_detection_enabled=settings.spam_detection_enabled,
    )

    normalized_articles = []
    for article in fetch_result.articles:
        normalized = await normalizer.normalize(article)
        if normalized:
            normalized_articles.append(normalized)

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

    # Step 5: Generate summaries (NEW STEP)
    summarizer = Summarizer(summary_style=summary_style)
    summarized_articles = []
    for article in scored_articles:
        summarized = await summarizer.summarize(article)
        summarized_articles.append(summarized)

    # Step 6: Detect similarity and group
    similarity_detector = SimilarityDetector()
    article_groups = await similarity_detector.detect_similar_articles(summarized_articles)

    return article_groups
```

## Implementation Design

### Summarizer Class

**Constructor:**
```python
def __init__(
    self,
    settings: Settings | None = None,
    ai_provider: AIProvider | None = None,
    summary_style: str = "brief",
)
```

**Parameters:**
- `settings`: Application settings (optional, uses get_settings() if not provided)
- `ai_provider`: AI provider instance (optional, creates from settings if not provided)
- `summary_style`: Summary style - "brief", "detailed", or "bullet_points" (default: "brief")

**Pydantic Models:**
```python
class SummaryResult(BaseModel):
    summary: str              # Concise summary of article content
    key_points: list[str]     # 3-5 key points or takeaways
    reasoning: str            # Explanation of summarization approach
```

**Main Methods:**
```python
# Public API
async def summarize(self, article: Article) -> Article

# Internal methods
def _build_system_prompt(self) -> str
def _build_summarization_prompt(self, article: Article) -> str
```

**Key Implementation Details:**
- ✅ **Single AI Agent** - `agent` for content summarization
- ✅ **Async methods** - Required for AI provider integration
- ✅ **Style-based system prompts** - Different prompts for each summary style
- ✅ **AI provider injection** - Uses AIProvider abstraction
- ✅ **Structured outputs** - Pydantic models for AI results with validation

**Key Design Principles:**
- **Async/Await:** Required for AI provider integration
- **Input:** Article → **Output:** Article (with summary populated)
- **Never raises exceptions:** Uses fallbacks and logs warnings
- **Dependency Injection:** AI provider can be injected for testing
- **Idempotent:** Running twice produces same result
- **Graceful Degradation:** Returns content excerpts on AI errors
- **Uses textwrap.dedent():** For clean prompts (see CLAUDE.md coding guidelines)

## Configuration Settings

**Location:** `app/config.py`

**Current Settings:**

```python
# Summarization Settings
summary_max_length: int = Field(500, env="SUMMARY_MAX_LENGTH")
summary_content_length: int = Field(2000, env="SUMMARY_CONTENT_LENGTH")
```

**Environment Variables:**
```bash
SUMMARY_MAX_LENGTH=500           # Maximum words in summary
SUMMARY_CONTENT_LENGTH=2000      # Maximum chars of content sent to AI
```

**Configuration Examples:**

```bash
# Brief summaries for quick reading
SUMMARY_MAX_LENGTH=300

# Detailed summaries with more context
SUMMARY_MAX_LENGTH=800

# Optimize for token efficiency
SUMMARY_CONTENT_LENGTH=1500
```

## Test Suite

**Location:** `tests/test_processors/test_summarizer.py`

**Current Status:** ✅ 18 tests implemented and passing

### Implemented Test Scenarios

1. ✅ **Summary Generation - Brief Style** - Successful brief summary creation
2. ✅ **Summary Generation - Detailed Style** - Successful detailed summary creation
3. ✅ **Summary Generation - Bullet Points Style** - Successful bullet points summary
4. ✅ **Topic Integration** - Uses topics from TopicExtractor
5. ✅ **Minimal Content Fallback** - Handles short articles without AI
6. ✅ **Empty Content Fallback** - Handles empty articles with title fallback
7. ✅ **AI Error Handling** - Graceful fallback on AI failures
8. ✅ **Content Truncation** - Verifies long content is truncated
9. ✅ **Model Validation** - SummaryResult Pydantic model validation
10. ✅ **System Prompt - Brief** - Brief style prompt building
11. ✅ **System Prompt - Detailed** - Detailed style prompt building
12. ✅ **System Prompt - Bullet Points** - Bullet points style prompt building
13. ✅ **Summarization Prompt Building** - Correct prompt construction
14. ✅ **Prompt with Tags** - Includes article tags in prompt
15. ✅ **Prompt without Tags** - Handles articles without tags
16. ✅ **Custom Summary Length** - Respects custom max length setting
17. ✅ **Multiple Articles** - Independent summarization of multiple articles
18. ✅ **Error Returns Article** - Errors return article with fallback, not None

### Test Structure

Tests use **async/await** pattern with mock AI provider for deterministic testing:

```python
@pytest.fixture
def mock_ai_provider(self):
    """Create a mock AI provider for testing."""
    mock_provider = MagicMock()

    def create_agent_mock(output_type, system_prompt):
        return Agent(TestModel(), output_type=output_type, system_prompt=system_prompt)

    mock_provider.create_agent = create_agent_mock
    return mock_provider

@pytest.mark.asyncio
async def test_summarize_brief_style_success(self, summarizer_brief, sample_articles):
    """Test successful brief summary generation."""
    test_model = TestModel(
        custom_output_args=SummaryResult(
            summary="Brief summary text...",
            key_points=["Point 1", "Point 2", "Point 3"],
            reasoning="Focused on core message"
        )
    )

    with summarizer_brief.agent.override(model=test_model):
        result = await summarizer_brief.summarize(sample_articles[0])
        assert result.summary is not None
        assert "key content" in result.summary
```

## Error Handling

The summarizer uses a **graceful degradation** strategy:

### Fallback Hierarchy

1. **Minimal/Empty Content** → Use excerpt or title (no AI call)
2. **AI Service Error** → Use first 300 chars of content
3. **Timeout Error** → Use first 300 chars of content
4. **Unexpected Error** → Use first 300 chars of content

**Example Error Handling:**

```python
try:
    # Run AI summarization
    result = await self.agent.run(prompt)
    summary_result = result.output

    # Format and store summary
    article.summary = summary_result.summary

except Exception as e:
    logger.error(f"Error generating summary: {e}")
    # Fallback to excerpt
    article.summary = article.content[:300] + "..."

return article  # Always returns article, never None
```

This ensures the pipeline continues processing even with AI failures.

## Performance Considerations

### Token Optimization

**Content Truncation:**
- Default: 2000 characters sent to AI (configurable)
- Balances context vs. token cost
- Sufficient for most article summarization

**Batch Processing:**
- Summarization can be parallelized across articles
- Each summarization is independent
- No cross-article dependencies

### Caching Opportunities (Future Enhancement)

**Potential Caching:**
- Cache summaries by content hash (Redis)
- Avoid re-summarizing same content
- TTL: 24-48 hours
- Key pattern: `summary:{content_hash}:{style}`

**Implementation Example:**
```python
# Check cache first
cache_key = f"summary:{hash(article.content)}:{self.summary_style}"
cached_summary = await redis.get(cache_key)

if cached_summary:
    article.summary = cached_summary
    return article

# Generate new summary
result = await self.agent.run(prompt)
article.summary = result.output.summary

# Cache for future use
await redis.setex(cache_key, 86400, article.summary)  # 24h TTL
```

## Integration with User Preferences

The summarizer supports user-configurable summary styles through digest configuration:

**DigestConfiguration Model:**
```python
class DigestConfiguration:
    summary_style: str  # "brief", "detailed", or "bullet_points"
```

**Usage in Workflow:**
```python
# In Temporal workflow
user_config = await fetch_user_config(user_id)
summary_style = user_config.summary_style  # From user preferences

# Create summarizer with user's preferred style
summarizer = Summarizer(summary_style=summary_style)

# Process articles
for article in articles:
    await summarizer.summarize(article)
```

## Success Criteria

### ✅ Achieved

- ✅ Summarizer processes articles consistently
- ✅ All summary styles implemented (brief, detailed, bullet points)
- ✅ All edge cases handled gracefully with fallbacks
- ✅ Test coverage: 18 comprehensive tests passing
- ✅ No exceptions raised during summarization (graceful degradation)
- ✅ Integration-ready for content processing pipeline
- ✅ Async architecture supports AI integration
- ✅ Logging provides visibility into summarization results
- ✅ Uses textwrap.dedent() for clean prompts (CLAUDE.md compliance)
- ✅ Proper dependency injection for testability

## Future Enhancements

### Advanced Features

**Multi-Language Support:**
- Detect article language
- Generate summaries in user's preferred language
- Translation integration

**Custom Summary Lengths:**
- Per-user word count preferences
- Dynamic length based on article complexity
- Mobile-optimized ultra-brief summaries

**Summary Quality Scoring:**
- Assess summary quality vs. original content
- Detect hallucinations or inaccuracies
- Re-summarize if quality is low

**Contextual Summaries:**
- User interest-aware summarization
- Focus on topics relevant to user profile
- Personalized emphasis

### Performance Optimizations

**Caching Strategy:**
- Redis caching by content hash
- Shared cache across users for same content
- Invalidation on content updates

**Batch Processing:**
- Batch multiple articles in single AI call
- Reduced API overhead
- Cost optimization

**Smart Truncation:**
- Intelligent content selection (not just first N chars)
- Extract most important paragraphs
- Better context for AI

## Related Documentation

- **AIProvider** (`app/processors/ai_provider.py`): AI provider abstraction used by summarizer
- **TopicExtractor** (`app/processors/topic_extractor.py`): Provides topics for enhanced summaries
- **QualityScorer** (`app/processors/quality_scorer.py`): Quality assessment for article prioritization
- **Content Processing** (`docs/content-processing.md`): Overall pipeline architecture
- **Configuration** (`docs/configuration.md`): Configuration management details

## Example Usage

### Basic Summarization

```python
from app.processors.summarizer import Summarizer
from app.processors.fetchers.base import Article

# Create summarizer
summarizer = Summarizer(summary_style="brief")

# Summarize article
article = Article(...)
summarized = await summarizer.summarize(article)

print(summarized.summary)
```

### Custom Configuration

```python
from app.config import Settings
from app.processors.summarizer import Summarizer

# Custom settings
custom_settings = Settings(
    database_url="postgresql://...",
    secret_key="...",
    summary_max_length=300,        # Shorter summaries
    summary_content_length=1500,   # Less content to AI
)

# Create summarizer with custom settings
summarizer = Summarizer(
    settings=custom_settings,
    summary_style="detailed"
)
```

### Different Summary Styles

```python
# Brief summary (1-2 paragraphs)
brief_summarizer = Summarizer(summary_style="brief")
brief_article = await brief_summarizer.summarize(article)

# Detailed summary (3-4 paragraphs)
detailed_summarizer = Summarizer(summary_style="detailed")
detailed_article = await detailed_summarizer.summarize(article)

# Bullet points summary
bullet_summarizer = Summarizer(summary_style="bullet_points")
bullet_article = await bullet_summarizer.summarize(article)
```

### Integration with Pipeline

```python
async def generate_digest(user_id: str):
    # Fetch user preferences
    user_config = await fetch_user_config(user_id)

    # Get articles
    articles = await fetch_articles(user_config.sources)

    # Normalize
    normalizer = ContentNormalizer()
    normalized = [await normalizer.normalize(a) for a in articles]

    # Score quality
    scorer = QualityScorer()
    scored = [await scorer.calculate_quality_score(a) for a in normalized]

    # Extract topics
    extractor = TopicExtractor()
    for article in scored:
        article.ai_topics = await extractor.extract_topics(article)

    # Generate summaries with user's preferred style
    summarizer = Summarizer(summary_style=user_config.summary_style)
    summarized = [await summarizer.summarize(a) for a in scored]

    # Detect similarity
    detector = SimilarityDetector()
    groups = await detector.detect_similar_articles(summarized)

    return groups
```
