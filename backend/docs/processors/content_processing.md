# Content Processing Pipeline

## Purpose

- Transform raw feed articles into digest-ready items.
- Provide deterministic ordering of processors and shared contracts for Temporal activities.
- Keep expensive AI calls cached/memoized to hit the 15-minute SLA.

## Execution Order

| Step | Module | Responsibility | Returns |
| --- | --- | --- | --- |
| 1 | `app/processors/fetchers/` | Pull raw articles from RSS/Atom (future: blogs). | `list[Article]` with minimal metadata. |
| 2 | `normalizer.py` | Validate content, sanitize HTML, normalize metadata. | `Article \| None` (drops spam/invalid). |
| 3 | `quality_scorer.py` | Calculate quality score (0–100). | `ContentQualityResult` with metadata/AI breakdown. |
| 4 | `topic_extractor.py` | Extract key topics from content. | `list[str]` of topics. |
| 5 | `relevance_scorer.py` | Score vs. user profile; flag threshold pass/fail. | `RelevanceResult` with score/breakdown/threshold. |
| 6 | `summarizer.py` | Produce summary matching user style. | `SummaryResult` with summary/key points/reasoning. |
| 7 | `similarity_detector.py` | Group semantically similar articles. | `list[ArticleGroup]` for digest assembly. |

**Immutability Contract**: Processors return new result objects and never mutate input articles. The pipeline orchestrator (Temporal workflow) aggregates results into the final article metadata.

## Inputs & Outputs

- **Input**: List of `Article` objects (post-fetch). Each article must include `url`, `title`, `content`, and `fetch_timestamp`; `published_at` is recommended for freshness scoring.
- **Output**: Processor-specific result objects that the pipeline orchestrator uses to build enriched articles:
  - `Normalizer`: Returns normalized `Article` copy (or `None` if rejected)
  - `QualityScorer`: Returns `ContentQualityResult` with quality score and breakdown
  - `TopicExtractor`: Returns `list[str]` of extracted topics
  - `RelevanceScorer`: Returns `RelevanceResult` with relevance score, breakdown, threshold status
  - `Summarizer`: Returns `SummaryResult` with summary, key points, reasoning
  - `SimilarityDetector`: Returns `list[ArticleGroup]` for clustering
- **Persistent side effects**: None. All state persists via Redis caches or downstream repositories.

## Dependencies

- `app/processors/ai_provider.py` supplies AI client; injected into any processor hitting AI.
- Redis (via `app/utils/cache.py`) memoizes expensive operations (`processor:{name}:{digest}`).
- Settings objects (see `docs/configuration.md`) passed explicitly to avoid global coupling.

## Failure Modes

- Fetch failure → raise `FetcherError`; Temporal activity handles retry or logs partial failure.
- Normalizer rejection → return `None`; upstream activity filters it out (never raises).
- AI timeout → processors log warning, return fallback result (quality=metadata only, summary=excerpt, similarity skip).
- Cache miss storm → ensure TTL staggering; consider pre-warming during off-peak.

## Integration Rules

- Always run processors in the order above; changing order requires updating both this doc and `temporal-workflows.md`.
- New processor? add to this table, document contract in its own file under `docs/processors/`, update Temporal activity.
- Follow the cache-key guidance in each processor doc (most use article URL + profile/config context); do not invent new hashing strategies without updating the documentation.

## Settings Reference

| Processor | Settings | Key Fields |
| --- | --- | --- |
| Fetchers | `RSSSettings` | `fetch_timeout`, `max_retries`, `retry_delay`, `max_articles_per_feed`, `user_agent`. |
| Normalizer | `ContentNormalizationSettings` | Length bounds, spam toggle, tag limits. |
| QualityScorer | `ContentNormalizationSettings.quality_scoring_enabled` | Enables AI quality pass. |
| TopicExtractor | `TopicExtractionSettings` | `max_topics`. |
| RelevanceScorer | `PersonalizationSettings` | Weights, thresholds, semantic toggle, cache ttl. |
| Summarizer | `SummarizationSettings`, `CustomPromptSettings`, `AIPromptValidationSettings` | Summary length, content truncation, prompt bounds. |
| SimilarityDetector | `SimilaritySettings` | `threshold`, `cache_ttl_minutes`, `batch_size`. |

Defaults and overrides for these settings live in `backend/docs/configuration.md`.

## Changelog

- **2025-10-12**: Phase 0 refactor complete - all processors now return immutable result objects; 182 tests passing.
- **2025-10-10**: Pipeline (fetch → normalize → score → summarize → group) stabilized; 170 processor tests green.
- **2025-09-25**: RSS fetcher shipped with retry + validation pipeline.
