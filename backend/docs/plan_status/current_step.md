# Personalization Pipeline Integration Plan

## Summary

Refactor processors so they stop mutating articles in-place, then stand up the missing Temporal scaffolding and wire the existing `RelevanceScorer` into a batch activity with a sane idempotency contract plus end‑to‑end metadata validation.

## Current State

### ✅ Phase 0 Complete: Processor Refactor (2025-10-12)

**Next**: Phase 1 - Temporal Infrastructure

### Implementation Plan

#### ✅ Phase 0: Processor Refactor (Complete)

**Implemented**:

1. ✅ Refactored all 6 processors to return result objects instead of mutating articles
2. ✅ Normalizer uses `article.model_copy(update={...})` for immutable transformations
3. ✅ Added dependency injection: RelevanceScorer accepts `quality_score`, Summarizer accepts `topics`
4. ✅ Updated 182 processor tests to match new signatures
5. ✅ Documented immutability contract in `common_patterns.md` and `content_processing.md`
6. ✅ Updated individual processor docs with new inputs/outputs/signatures

**Result Models**:

- `ContentQualityResult`: quality scores + breakdown
- `RelevanceResult`: relevance score + detailed breakdown + threshold status
- `SummaryResult`: summary + key points + reasoning
- Topic/Similarity processors return native Python types (`list[str]`, `list[ArticleGroup]`)

#### Phase 1: Temporal Infrastructure

1. Create foundational package layout:

```text
app/temporal/
├── __init__.py
├── activities/
│   ├── __init__.py
│   └── processing.py        # processor-driven activities live here
├── client.py                # helpers for starting Temporal client when needed
└── shared.py                # shared activity utilities (timeouts, logging hooks)
```

- Ensure dependency injection mirrors existing processor usage (settings + cache helpers).
- Share activity option presets (timeout/retry classes) so future activities reuse the same constants.

2. Add lightweight smoke tests to confirm the package imports cleanly (no Temporal worker launch yet).

#### Phase 2: Relevance Activity Contract

3. Define the activity surface in `activities/processing.py` without implementation:
     - Decide on function signature (e.g., `score_relevance_batch(profile: InterestProfile, articles: list[Article]) -> list[Article]`).
     - Document idempotency via the cache key (`profile.id` + `article.url`) rather than metadata presence.
     - Capture timeout/retry options referencing `docs/temporal-workflows.md`.
4. Add unit tests covering the idempotency guard logic (verifies cached entries bypass re-score).

#### Phase 3: Activity Implementation & Tests

5. Implement `score_relevance_batch`:
     - Initialize `RelevanceScorer` with injected cache/settings (reuse existing factory/helpers).
     - Score each article sequentially, ensuring prior metadata persists.
     - Use the cache key check to short-circuit already-scored pairs.
     - Wrap AI provider errors and surface retryable exceptions as needed.
6. Expand `tests/test_temporal/test_activities_processing.py`:
     - Test activity with real `RelevanceScorer` (no Temporal overhead)
     - Verify metadata fields are correctly added to articles
     - Test idempotency (calling twice with same profile/article reuses cached result)
     - Test with empty profile (should pass threshold)
     - Test threshold filtering behavior
     - Validate error handling when AI fails

#### Phase 4: Integration Verification

7. Add end-to-end metadata propagation test:
     - Run full processing chain: normalize → quality → topic → relevance
     - Verify `relevance_score`, `relevance_breakdown`, `passes_relevance_threshold` present
     - Confirm prior processor metadata (`quality_score`, `ai_topics`) preserved
     - Exercise cache warm + reuse path to ensure metadata sticks.

#### Phase 5: Workflow Integration (Optional for MVP)

8. Create minimal `daily_digest` workflow stub in `workflows/digest.py`:
     - Define workflow that will call activities in sequence once they exist:
       - `fetch_sources` → `normalize_articles` → `score_quality` → `extract_topics` → `score_relevance` → `summarize`
     - Keep calls behind `NotImplementedError` placeholders so imports succeed without full implementations.
     - Document that this stub remains disabled until upstream activities ship.

#### Phase 6: Documentation Updates

9. Toggle `docs/temporal-workflows.md` activity rows from “planned” to “implemented” once modules land.
10. Update `docs/processors/content_processing.md` and `docs/processors/relevance_scorer.md` with concrete references to the new activity and cache behavior.
11. Update `backend/docs/plan_status/status_board.md` when integration reaches green status.

### Success Criteria

- ✅ Processor refactor complete: processors return new objects, no in-place mutations
- ✅ All 182 processor tests passing
- ✅ Documentation updated: `common_patterns.md`, `content_processing.md`, 4 processor docs
- ❌ Temporal scaffolding exists (`app/temporal/` package with shared helpers)
- ❌ Activity `score_relevance_batch` exists in `app/temporal/activities/processing.py`
- ❌ Activity passes 6+ integration tests covering happy path, idempotency, errors
- ❌ Metadata fields flow correctly through pipeline orchestrator
- ❌ Idempotency verified: cache guard (`profile.id` + `article.url`) prevents redundant scoring
- ❌ Documentation updated in remaining places (`temporal-workflows.md`, `status_board.md`)

### Out of Scope (Tracked Separately)

- Actual Temporal worker implementation (separate workstream)
- Digest assembly using relevance metadata (tracked as "Digest assembly enhancements")
- Quality scorer / summarizer caching (separate pending items)
- Metrics / telemetry (blocked pending sink selection)
