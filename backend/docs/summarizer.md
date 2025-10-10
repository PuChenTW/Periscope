# Article Summarization Module

## Overview

The Article Summarization module provides AI-powered article summarization to generate concise, user-friendly summaries for the daily digest. It supports multiple summary styles (brief, detailed, bullet points) and integrates seamlessly with the content processing pipeline.

**Location:** `app/processors/summarizer.py`

**Status:** Implemented

**Pipeline Position:**
```
RSS Fetcher → Normalizer → QualityScorer → TopicExtractor → Summarizer → SimilarityDetector → Digest
```

## Key Features
- **AI-Powered Summarization**: Uses PydanticAI with configurable AI providers
- **Multiple Summary Styles**: Brief, detailed, and bullet points formats
- **Configurable Length Limits**: Customizable max word count per summary
- **Content Truncation**: Efficient token usage
- **Graceful Degradation**: Fallback to content excerpts on AI errors
- **Topic Integration**: Uses topics from TopicExtractor for enhanced context
- **Async Architecture**: Full async/await support
- **Dependency Injection**: Constructor-based configuration

## Key Features & Usage

### 1. Summary Styles

The summarizer supports three different summary styles based on user preferences:

#### Brief Style (Default)
**Purpose:** Quick overview for busy readers

**Characteristics:**
- Concise paragraphs
- Focuses on core message
- Simple, clear sentences

**Use Case:** Quick daily updates

#### Detailed Style
**Purpose:** Comprehensive understanding

**Characteristics:**
- Multiple paragraphs with context
- Covers multiple aspects
- Explains technical terms when needed

**Use Case:** Deeper insights

#### Bullet Points Style
**Purpose:** Scannable key information

**Characteristics:**
- List of key points
- Self-contained items
- Organized by importance

**Use Case:** Structured, scannable summaries

### 2. AI-Powered Summarization

**Process:**
1. Article content is truncated to configurable length
2. Context includes title, tags, and AI-extracted topics
3. AI generates structured summary based on style
4. Summary is formatted according to style preferences
5. Result is stored in article.summary field

### 3. Fallback Strategies

The summarizer uses multiple fallback strategies to ensure robustness:

**Minimal Content Handling:**
- Short articles: Use excerpt without AI call
- Empty content: Use article title as fallback

**AI Error Handling:**
- AI service failures: Use content excerpt
- Timeout errors: Graceful fallback to excerpt
- Never raises exceptions - always returns article with summary

### 4. Integration with Content Pipeline

The summarizer integrates with other processors for enhanced results:

**Topic Extractor Integration:**
- Uses `article.ai_topics` for additional context
- Topics inform summarization focus
- Improves relevance and accuracy

**Quality Scorer Integration:**
- Can prioritize high-quality articles for summarization
- Quality scores can influence summary style selection

**Pipeline Position:**
1. Fetch and normalize articles
2. Calculate quality scores
3. Extract topics
4. **Generate summaries** (Summarizer)
5. Detect similarity and group articles

## Implementation Design

### Summarizer Class

**Main Methods:**
- `summarize()`: Public API for article summarization
- `_build_system_prompt()`: Style-specific prompt generation
- `_build_summarization_prompt()`: Article-specific prompt building

**Key Design Principles:**
- **Async/Await:** Required for AI provider integration
- **Input:** Article → **Output:** Article (with summary populated)
- **Never raises exceptions:** Uses fallbacks and logs warnings
- **Dependency Injection:** AI provider can be injected for testing
- **Idempotent:** Running twice produces same result
- **Graceful Degradation:** Returns content excerpts on AI errors

## Configuration Settings

**Location:** `app/config.py`

**Current Settings:**

- `SUMMARY_MAX_LENGTH`: Maximum words in summary
- `SUMMARY_CONTENT_LENGTH`: Maximum chars of content sent to AI

## Test Coverage

Tests use async/await pattern with mock AI provider covering:
- Summary generation for all styles (brief, detailed, bullet points)
- Topic integration
- Minimal content and empty content fallbacks
- AI error handling
- Content truncation
- Prompt building for different styles
- Edge cases and error scenarios

## Error Handling

The summarizer uses a **graceful degradation** strategy:

### Fallback Hierarchy

1. **Minimal/Empty Content** → Use excerpt or title (no AI call)
2. **AI Service Error** → Use content excerpt
3. **Timeout Error** → Use content excerpt
4. **Unexpected Error** → Use content excerpt

This ensures the pipeline continues processing even with AI failures.

## Performance Considerations

### Token Optimization

**Content Truncation:**
- Configurable character limit sent to AI
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
- Configurable TTL
- Key pattern: `summary:{content_hash}:{style}`

## Integration with User Preferences

The summarizer supports user-configurable summary styles through digest configuration. Users can choose their preferred style (brief, detailed, or bullet_points), and the Temporal workflow will create a summarizer with that style.

## Related Documentation

- **AIProvider** (`app/processors/ai_provider.py`): AI provider abstraction
- **TopicExtractor** (`app/processors/topic_extractor.py`): Provides topics for enhanced summaries
- **QualityScorer** (`app/processors/quality_scorer.py`): Quality assessment for article prioritization
- **Content Processing** (`docs/content-processing.md`): Overall pipeline architecture
- **Configuration** (`docs/configuration.md`): Configuration management
