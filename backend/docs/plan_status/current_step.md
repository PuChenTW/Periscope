# Personalization Pipeline Integration Plan

## Summary

Refactor processors so they stop mutating articles in-place, then stand up the missing Temporal scaffolding and wire the existing `RelevanceScorer` into a batch activity with a sane idempotency contract plus end‑to‑end metadata validation.

## Current State

### ✅ Already Complete

- `RelevanceScorer` implemented with 26 passing tests (`app/processors/relevance_scorer.py`)
- Adds 3 metadata fields to articles: `relevance_score`, `relevance_breakdown`, `passes_relevance_threshold`
- `InterestProfile` database model exists with `keywords`, `threshold`, `boost_factor`
- All dependencies in place (settings, cache, AI provider)

### ❌ Missing (Blocks Integration)

- No Temporal infrastructure (`app/temporal/` directory doesn't exist)
- No `score_relevance` activity wrapper
- No integration tests validating metadata flow
- No workflow to orchestrate the activity

### Implementation Plan

#### Phase 0: Processor Refactor

1. Audit each processor (`normalizer`, `quality_scorer`, `topic_extractor`, `relevance_scorer`, `summarizer`, `similarity_detector`) to ensure they return new article payloads instead of mutating the original input object.
2. Introduce a lightweight `ProcessedArticle` data structure (or copy-on-write helper) so metadata aggregation happens in the pipeline orchestrator, not individual processors.
3. Update unit tests and fixtures to assert immutability (original article untouched, processed output contains modifications).
4. Document the immutability contract in `docs/processors/common_patterns.md` and `docs/processors/content_processing.md`.

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

- Processor refactor complete: processors return new objects and pipeline handles metadata aggregation
- Temporal scaffolding exists (`app/temporal/` package with shared helpers)
- Activity `score_relevance_batch` exists in `app/temporal/activities/processing.py`
- Activity passes 6+ integration tests covering happy path, idempotency, errors
- Metadata fields (`relevance_score`, `relevance_breakdown`, `passes_relevance_threshold`) flow correctly
- Idempotency verified: cache guard (`profile.id` + `article.url`) prevents redundant scoring
- Documentation updated in 3 places (`temporal-workflows.md`, `content_processing.md`, `status_board.md`)
- All existing tests still pass (`uv run pytest`)

### Out of Scope (Tracked Separately)

- Actual Temporal worker implementation (separate workstream)
- Digest assembly using relevance metadata (tracked as "Digest assembly enhancements")
- Quality scorer / summarizer caching (separate pending items)
- Metrics / telemetry (blocked pending sink selection)
