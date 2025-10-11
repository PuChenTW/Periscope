# RelevanceScorer

## Purpose

- Personalize articles per user by scoring relevance (0–100) using keyword hits + optional AI semantic lift.

## Inputs

- `Article` post QualityScorer with: `title`, `content`, `tags`, `ai_topics`, `metadata["quality_score"]`, `published_at`.
- `InterestProfile` (keywords, boost factor, threshold).
- `PersonalizationSettings`.

## Outputs

- `article.metadata["relevance_score"]`
- `article.metadata["relevance_breakdown"]` (keyword matches, semantic score, boosts)
- `article.metadata["passes_relevance_threshold"]` (bool)

## Dependencies

- AI provider (only when `enable_semantic_scoring=True` and deterministic score ambiguous).
- Redis cache key `relevance:{profile_id}:{article.url}` (12 h TTL) to skip re-scoring.
- `normalize_term_list()` from `app/utils/text_processing.py` for token cleanup.
- Settings: see personalization section in `backend/docs/configuration.md`.

## Scoring Flow

1. **Keyword stage (0–60)**: Build keyword index, weight matches (title=3, content=2, tags/topics=4).
2. **Semantic stage (0–30)**: If keywords exist and score within ambiguity window, call AI for semantic match.
3. **Boost stage (0–10)**: Freshness (≤24h) + quality score bonus (≥80) when keywords hit.
4. Apply user `boost_factor`, clamp 0–100, compare to `relevance_threshold`.

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

- **2025-10-10**: Initial implementation with full test suite (26 cases) and Redis caching.
