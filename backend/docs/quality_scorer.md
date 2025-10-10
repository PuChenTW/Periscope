# Content Quality Scoring Module

## Overview

The Content Quality Scoring module provides hybrid quality assessment for articles by combining rule-based metadata scoring with AI-powered content quality analysis. This produces a final quality score (0-100 scale) used for article ranking, filtering, and prioritization in the content pipeline.

**Location:** `app/processors/quality_scorer.py`

**Status:** Implemented

**Pipeline Position:**
```
RSS Fetcher → ContentNormalizer → QualityScorer → TopicExtractor → SimilarityDetector → Summarizer → Digest
```

## Key Features
- **Hybrid Quality Scoring**: Rule-based metadata scoring + AI-powered content assessment
- **Metadata Scoring**: Objective completeness metrics
- **AI Content Quality**: Subjective quality assessment using PydanticAI
- **AI Provider Integration**: Uses configurable AI provider abstraction
- **Async Architecture**: Full async/await support
- **Dependency Injection**: Constructor-based configuration
- **Graceful Degradation**: Falls back to metadata-only scoring when AI disabled

## Key Features & Usage

### 1. Hybrid Quality Scoring

**Purpose:** Ranks articles by combining objective metadata completeness with subjective content quality

**Implementation:** Two-component hybrid scoring system

#### Rule-Based Component
**Metadata Completeness Scoring:**
- Has author
- Has published date
- Has tags
- Content length thresholds
- Additional bonuses for comprehensive content

#### AI-Powered Component
**Content Quality Assessment using PydanticAI:**

- **Writing Quality**: Clarity, coherence, grammar, structure, readability
- **Informativeness**: Depth, coverage, value, insights, specific details
- **Credibility**: Evidence, balanced perspective, professional tone

**Final Score:** Combined metadata and AI content scores

**Configuration:**
- `quality_scoring_enabled`: Toggle AI quality assessment
- When disabled, metadata score is scaled appropriately

**Why Hybrid Approach:**
- Fast rule-based metrics for objective completeness
- Deep AI analysis for subjective content quality
- Balanced scoring resistant to manipulation
- Graceful degradation when AI unavailable

**Storage:**
Scores stored in `article.metadata` with quality breakdown

## Implementation Design

### QualityScorer Class

**Main Methods:**
- `calculate_quality_score()`: Public API for scoring articles
- `_calculate_metadata_score()`: Internal metadata scoring
- `_assess_content_quality()`: Internal AI quality assessment

**Key Design Principles:**
- **Async/Await:** Required for AI provider integration
- **Input:** Article → **Output:** Article (with quality_score in metadata)
- **Never raises exceptions:** Uses fallbacks and logs warnings
- **Dependency Injection:** AI provider can be injected for testing
- **Idempotent:** Running twice produces same result
- **Graceful Degradation:** Returns neutral scores on AI errors

## Configuration Settings

**Location:** `app/config.py`

**Current Settings:**

- `quality_scoring_enabled`: Enable AI-powered quality assessment

## Test Coverage

Tests use async/await pattern with mock AI provider for deterministic testing covering:
- Metadata score calculation
- Hybrid scoring with AI
- Scoring with AI disabled
- Edge cases and error handling

## Integration with Content Pipeline

### Usage in Processing Pipeline

The quality scorer integrates into the content processing pipeline:

1. Fetch content from sources
2. Normalize articles (spam detection, metadata standardization)
3. **Calculate quality scores** (QualityScorer)
4. Extract topics
5. Detect similarity and group articles

### Error Handling

The quality scorer uses a **graceful degradation** strategy:

- **AI scoring disabled:** Falls back to metadata-only scoring
- **AI assessment errors:** Returns neutral scores
- **Unexpected errors:** Catches and logs, returns neutral scores

This ensures the pipeline continues processing even with AI failures.

## Architecture Notes

The quality scoring module is decoupled from ContentNormalizer to maintain single responsibility:
- `ContentNormalizer`: Data validation and metadata standardization
- `QualityScorer`: Article quality assessment

This separation improves testability, reusability, and maintainability.
