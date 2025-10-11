# Content Processing Pipeline

## Purpose

- Transform raw feed articles into digest-ready items.
- Provide deterministic ordering of processors and shared contracts for Temporal activities.
- Keep expensive AI calls cached/memoized to hit the 15-minute SLA.

## Execution Order

| Step | Module | Responsibility | Notes |
| --- | --- | --- | --- |
| 1 | `app/processors/fetchers/` | Pull raw articles from RSS/Atom (future: blogs). | Uses `RSSFetcher`; emits `Article` objects with minimal metadata. |
| 2 | `normalizer.py` | Validate content, sanitize HTML, normalize metadata. | Drops spam/invalid articles; no DB writes. |
| 3 | `quality_scorer.py` | Attach `metadata["quality_score"]` (0–100). | Hybrid rule-based + AI; see dedicated doc. |
| 4 | `topic_extractor.py` | Populate `article.ai_topics`. | Cached by article digest + settings. |
| 5 | `relevance_scorer.py` | Score vs. user profile; flag threshold pass/fail. | Semantic step optional via settings. |
| 6 | `summarizer.py` | Produce summary matching user style. | Falls back to excerpt on AI failure. |
| 7 | `similarity_detector.py` | Group semantically similar articles. | Returns cluster ids for digest assembly. |

Processors mutate the `Article` in-place and append diagnostic info to `article.metadata`.

## Inputs & Outputs

- **Input**: List of `Article` objects (post-fetch). Each article must include `source_id`, `url`, `title`, `content`, `published_at`.
- **Output**: List of processed `Article` objects + similarity cluster map consumed by digest assembly.
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
- Use `Article.digest()` (SHA1 of title+url) for cache keys; never invent new hashing strategy per processor.

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

- **2025-10-10**: Pipeline (fetch → normalize → score → summarize → group) stabilized; 170 processor tests green.
- **2025-09-25**: RSS fetcher shipped with retry + validation pipeline.
