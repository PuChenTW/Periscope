# RelevanceScorer

## Purpose

- Personalize articles per user by scoring relevance (0–100) using keyword hits + optional AI semantic lift.

## Inputs

- `Article` with: `title`, `content`, `tags`, `ai_topics`, `published_at`, `summary`.
- `InterestProfile` (keywords, boost factor, threshold).
- `quality_score: int | None` (optional dependency from QualityScorer, used for quality boost).
- `PersonalizationSettings`.

## Outputs

Returns `RelevanceResult` with:

- `relevance_score: int` (0-100, final relevance after all boosts)
- `breakdown: RelevanceBreakdown` with:
  - `keyword_score: int` (0-60, deterministic keyword matching)
  - `semantic_score: float` (0-30, optional AI semantic analysis)
  - `temporal_boost: int` (0-5, freshness bonus for articles ≤24h)
  - `quality_boost: int` (0-5, bonus for high-quality articles with keyword matches)
  - `final_score: int` (total before clamping)
  - `matched_keywords: list[str]` (which profile keywords matched)
  - `threshold_passed: bool` (comparison result)
- `passes_threshold: bool` (whether score ≥ profile threshold)
- `matched_keywords: list[str]` (copy for convenience)

**Note**: Does not mutate input article. Accepts `quality_score` as parameter for dependency injection.

## Dependencies

- AI provider (only when `enable_semantic_scoring=True` and deterministic score ambiguous).
- Redis cache key `relevance:{profile_id}:{article.url}` (12 h TTL) to skip re-scoring.
- `normalize_term_list()` from `app/utils/text_processing.py` for token cleanup.
- Settings: see personalization section in `backend/docs/configuration.md`.

## Scoring Flow

1. **Keyword stage (0–60)**: Build keyword index from title/content/tags, weight matches (title=3, content=2, tags/topics=4), clamp to 60 max.
2. **Semantic stage (0–30)**: If score in ambiguity window (16-54) and semantic enabled, call AI with article summary + topics for deeper understanding.
3. **Boost stage (0–10)**:
   - **Temporal**: Articles ≤24h old get linear decay bonus (0-5 points)
   - **Quality**: Articles with quality_score ≥80 AND keyword matches get +5 points
4. Apply user `boost_factor` (0.5-2.0x multiplier), clamp 0–100, compare to `relevance_threshold`.
5. **Cache**: Store `RelevanceResult` in Redis with key `relevance:{profile_id}:{article_url}` (12h TTL).

**Empty Profile Handling**: When profile has no keywords, returns score=0 but `passes_threshold=True` to keep content flowing.

## Failure Modes

- Shared behaviours: `backend/docs/processors/common_patterns.md`.
- Additional specifics:
  - Empty keyword list → score 0 but mark threshold pass to keep content flowing (INFO).
  - Semantic stage skipped when ambiguity logic short-circuits (DEBUG).

## Metrics & Instrumentation

- Planned metrics (`relevance.keyword_only`, `relevance.semantic_calls`, `relevance.ai_failures`) to be added once telemetry workstream unblocked.
- Logs include `profile_id`, `article_url`, `keyword_score`, `semantic_score`, `boost`.

## Tests

- `backend/tests/test_processors/test_relevance_scorer.py`

## Changelog

- **2025-10-12**: Refactored to return `RelevanceResult` and accept `quality_score` as parameter; updated cache to serialize result objects.
- **2025-10-10**: Initial implementation with full test suite (26 cases) and Redis caching.
