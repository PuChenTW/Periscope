# Relevance Scoring Processor Design

## Implementation Status

**Status**: ✅ COMPLETED
**Completion Date**: 2025-10-10
**Test Coverage**: 26/26 tests passing
**Location**: `app/processors/relevance_scorer.py`

## Why We Need This

- Personalization is now implemented in the pipeline; relevance scoring enables users to receive personalized ranked feeds.
- Relevance is deterministic, cheap, and explainable with optional AI semantic scoring to enhance accuracy.
- The processor feeds both digest assembly (filtering below threshold) and ranking (boosting high-scoring articles).

## Inputs, Outputs, Constraints

- **Inputs**
    - `Article` objects coming out of normalization and quality scoring. We rely on: `title`, `content`, `tags`, `ai_topics`, `metadata["quality_score"]`, `published_at`.
    - `InterestProfile` attached to the user digest configuration. Keywords are stored as a JSON array with 50-keyword maximum after trimming and deduplication.
    - User overrides: `relevance_threshold`, `boost_factor`. Both are stored in the InterestProfile model in the database.
- **Outputs**
    - `Article.metadata["relevance_score"]` in the 0–100 range.
    - `Article.metadata["relevance_breakdown"]` with per-component scores and matched keywords for explainability.
    - Boolean `Article.metadata["passes_relevance_threshold"]` for downstream filtering.
- **Operational Constraints**
    - Must run per `(article, user)` pair inside the personalization step; worst case 20 sources × 50 articles × 1 000 users → keep it under ~25 ms per article without AI. AI path must stay under 250 ms. Two-step scoring lets us short-circuit when deterministic score is obviously high/low.
    - No extra abstraction layer; a single `RelevanceScorer` class with pure helper functions keeps things testable.

## Scoring Model

- **Stage 1 — Keyword Match (0–60 points)**
    - Lowercase + strip punctuation on both article text and keywords.
    - Count unique keyword hits in title (weight 3), summary/content snippet (weight 2), tags/topics (weight 4).
    - Clamp to 60 points. This stage is synchronous and runs for every article. If score ≥ 55 we skip AI; if ≤ 15 we mark as low and call AI only when the user has `boost_factor > 1.0`.
- **Stage 2 — Semantic Lift (0–30 points)**
    - Only run when keywords exist and the article survived the low-score cutoff.
    - Prompt the existing `AIProvider` with: normalized keywords, article title, 1st 800 chars of content, existing summary (if already generated), and `ai_topics`.
    - Output model: `semantic_score` (0–30), `matched_interests` (top 5 strings), `reasoning`.
    - On timeout/error: return 0 and reason `"ai_error"`; deterministic score stands.
- **Stage 3 — Temporal & Quality Boost (0–10 points)**
    - Fresh content (<= 24h) adds up to 5 points linearly; high quality (metadata `quality_score` ≥ 80) adds up to 5 more if at least one keyword matched.
- **Final Score**
    - Sum stages, clamp 0–100.
    - Apply optional user `boost_factor` (default 1.0) with clamp.
    - Compare to `relevance_threshold` (default 40). Store pass/fail for downstream filtering in digest assembly.

## Processor Shape

- **Constructor** takes optional `PersonalizationSettings`, injected `AIProvider`, and a callable that fetches the user profile (for reuse in tests).
- **Public coroutine** `score_article(article, profile)` mutates the article metadata in place and returns the article.
- **Helpers** stay private pure functions (`_build_keyword_index`, `_score_keyword_matches`, `_should_run_ai`, `_build_semantic_prompt`, `_apply_temporal_quality_boost`), with keyword normalization handled by `normalize_term_list()`.
- **Pydantic Models**
    - `SemanticRelevanceResult` with `semantic_score`, `matched_interests`, `reasoning`, `confidence`.
    - `RelevanceBreakdown` to serialize keyword hits, semantic info, boosts, threshold.
- **Caching**
    - Redis key: `relevance:{profile_id}:{article.digest}` (digest = sha1 of title + url). TTL 12 h.
    - Cache stores the full breakdown; bypass AI when cached and content digest unchanged.

## Error Handling & Observability

- No silent failures. Log at `warning` when AI fails, at `info` for cache hits/misses (debug build only).
- Emit metrics: `relevance.keyword_only`, `relevance.semantic_calls`, `relevance.ai_failures`, `relevance.avg_score`.
- On malformed profile (empty keyword list) return 0 and set `passes_relevance_threshold = True` so users without interests still see content.

## Implementation Summary

All planned implementation steps have been completed:

1. **Config plumbing** ✅ COMPLETED

   - Added `PersonalizationSettings` to `app/config.py` with weights, thresholds, cache TTL, and enable_semantic_scoring flag.
   - Wired settings into `get_settings()` with environment variable overrides documented.

2. **Data preparation** ✅ COMPLETED

   - Extended `InterestProfile` model in `app/models/users.py` to store `relevance_threshold` (int) and `boost_factor` (float, default 1.0).
   - Implemented parser helper `normalize_term_list()` in `app/utils/text_processing.py` for keyword normalization.

3. **Processor** ✅ COMPLETED

   - Created `app/processors/relevance_scorer.py` implementing the full three-stage scoring algorithm.
   - Integrated Redis caching using shared utilities with 12-hour TTL.
   - Implemented all helper functions for keyword matching, semantic scoring, and boost calculations.

4. **Pipeline integration** 🚧 PENDING

   - Scorer ready for integration into personalization activity after quality scoring.
   - Digest assembler integration pending (respects `passes_relevance_threshold` for filtering).

5. **Testing** ✅ COMPLETED

   - Full test suite in `tests/test_processors/test_relevance_scorer.py` with 26 passing tests.
   - Coverage includes: keyword scoring, semantic AI integration, boosts, thresholds, caching, error handling, empty profiles.
   - Mock AI provider tests verify prompt structure and semantic score integration.

6. **Telemetry** ⚠️ PARTIAL

   - Logging integrated for cache hits/misses, AI calls, and error conditions.
   - Metrics and operational documentation update deferred per user request.

## Open Questions

- ✅ RESOLVED: AI usage is gated via `enable_semantic_scoring` flag in PersonalizationSettings (environment variable: `PERSONALIZATION__ENABLE_SEMANTIC_SCORING`).
- 🚧 PENDING: Digest assembly integration to ensure relevance metadata persists with `Article` objects through serialization.

## Implementation Checklist

- ✅ Config + settings additions merged.
- ✅ Database/API changes for interest profile implemented (InterestProfile model extended).
- ✅ Processor + tests implemented and passing (26/26 tests).
- 🚧 Personalization pipeline integration pending.
- ⚠️ Operations doc update deferred per user request.
