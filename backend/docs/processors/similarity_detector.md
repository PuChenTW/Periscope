# SimilarityDetector

## Purpose

- Cluster processed articles that cover the same story so the digest can collapse duplicates.

## Inputs

- List of normalized `Article` objects (should already include `ai_topics` from TopicExtractor).
- `SimilaritySettings` (see similarity section in `backend/docs/configuration.md`).
- `CacheProtocol` instance (Redis cache is provided in production).
- AI provider (defaults via `create_ai_provider(get_settings())`).

## Outputs

- Returns `list[ArticleGroup]` with `primary_article`, `similar_articles`, `common_topics`, `group_id`.
- Updates are in-memory only; caller persists grouping metadata as needed.

## Dependencies

- PydanticAI agent for pairwise comparisons.
- Cache stores `{"is_similar": bool}` per article pair using SHA256 keys.
- Uses `Article.ai_topics` to populate `common_topics`.

## Hot Path / Algorithm

1. Short-circuit: 0 articles → `[]`; 1 article → single group with empty `similar_articles`.
2. For each article pair, build prompt (truncate content to 500 chars) and call AI unless cache hit.
3. Treat confidence ≥ `settings.threshold` as similar; populate adjacency graph.
4. Run DFS over graph to build connected components.
5. For each component, select first article as primary, merge topics, emit `ArticleGroup` with stable ID (SHA256 of URLs).

## Failure Modes

- Shared behaviours: `backend/docs/processors/common_patterns.md`.
- Processor-specific:
  - Cache retrieval/set failures → log warning, continue without cache.
  - AI failure → log error and treat pair as NOT similar (prevents false positives).

## Metrics & Instrumentation

- Planned: `similarity.ai_calls_total`, `similarity.cache_hits_total`. Not yet wired.

## Settings

- `SimilaritySettings.threshold` (pairwise confidence floor).
- `SimilaritySettings.cache_ttl_minutes` (pair result lifetime).
- `SimilaritySettings.batch_size` (future batching heuristic, not yet consumed).

## Tests

- `backend/tests/test_processors/test_similarity_detector.py`.

## Changelog

- **2025-10-10**: Graph-based similarity grouping shipped with cache integration.
