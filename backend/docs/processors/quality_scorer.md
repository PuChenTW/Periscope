# QualityScorer

## Purpose

- Produce a 0–100 quality score for each article so downstream stages can rank/filter content.

## Inputs

- `Article` from Normalizer with fields: `title`, `content`, `author`, `published_at`, `tags`.
- `ContentNormalizationSettings` (for limits) and injected AI provider.

## Outputs

Returns `ContentQualityResult` with:

- `quality_score: int` (0-100, total quality)
- `metadata_score: int` (0-50, rule-based metadata completeness)
- `ai_content_score: int` (0-50, AI assessment of writing/informativeness/credibility)
- `reasoning: str` (explanation of assessment)

**Note**: Does not mutate input article. Pipeline orchestrator uses this result to enrich article metadata.

## Dependencies

- AI provider created via `ai_provider.create_ai_provider()` when `CONTENT__QUALITY_SCORING_ENABLED` is true (see `backend/docs/configuration.md`).
- Redis cache optional (future enhancement). Currently the scorer runs per article invocation.

## Hot Path

1. Compute metadata score (author, publish date, tags, length bonuses): 0-50 points.
2. If AI enabled, call provider with truncated content (first 1500 chars) to assess:
   - Writing quality (0-20): clarity, grammar, structure
   - Informativeness (0-20): depth, coverage, value
   - Credibility (0-10): sources, balance, professionalism
3. Combine scores: `metadata_score + ai_content_score` (max 100).
4. When AI disabled: scale metadata score to 0-100 range (`metadata_score * 2`).
5. Return `ContentQualityResult` with breakdown for transparency.

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

- **2025-10-12**: Refactored to return `ContentQualityResult` instead of mutating article metadata.
- **2025-10-10**: Hybrid scoring (rule + AI) shipped with async support.
