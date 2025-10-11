# QualityScorer

## Purpose

- Produce a 0–100 quality score for each article so downstream stages can rank/filter content.

## Inputs

- `Article` from Normalizer with fields: `title`, `content`, `author`, `published_at`, `metadata`.
- `ContentNormalizationSettings` (for limits) and injected AI provider.

## Outputs

- Sets `article.metadata["quality_score"]`.
- Stores breakdown under `article.metadata["quality_breakdown"]` (rule vs. AI components).

## Dependencies

- AI provider created via `ai_provider.create_ai_provider()` when `CONTENT__QUALITY_SCORING_ENABLED` is true (see `backend/docs/configuration.md`).
- Redis cache optional (future enhancement). Currently the scorer runs per article invocation.

## Hot Path

1. Compute metadata score (author, publish date, tags, length bonuses).
2. If AI enabled, call provider with truncated content to assess writing quality, informativeness, credibility.
3. Combine scores (weighted 50/50), clamp 0–100, add to metadata.
4. On repeated runs with same metadata, idempotently overwrite with same value.

## Failure Modes

- Shared behaviours are defined in `backend/docs/processors/common_patterns.md`.
- Additional specifics:
  - Missing essential fields (e.g., empty content) → returns score 0, marks `reason="insufficient_content"` (WARN).

## Metrics & Instrumentation

- Emits (planned) metric `quality.score` with labels `{source}` and histogram bins (todo in telemetry workstream).
- Logs include `article_digest`, `metadata_score`, `ai_score`.

## Tests

- `backend/tests/test_processors/test_quality_scorer.py` (metadata + AI scoring, fallbacks).

## Changelog

- **2025-10-10**: Hybrid scoring (rule + AI) shipped with async support.
