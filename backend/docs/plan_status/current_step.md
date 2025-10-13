# Personalization Pipeline Integration Plan

## Summary

Refactor processors so they stop mutating articles in-place, then stand up the missing Temporal scaffolding and wire the existing `RelevanceScorer` into a batch activity with a sane idempotency contract plus end‑to‑end metadata validation.

## Current State

### ✅ Phase 0 Complete: Processor Refactor (2025-10-12)

### ✅ Phase 1 Complete: Temporal Infrastructure (2025-10-12)

### ✅ Phase 1.5 Complete: Critical Integration Fixes (2025-10-12)

**Status**: All blocking issues resolved. Infrastructure ready for Phase 2 implementation.

**Next**: Phase 2 - Relevance Activity Implementation

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

#### ✅ Phase 1: Temporal Infrastructure (Complete)

1. ✅ Created foundational package layout:

```text
app/temporal/
├── __init__.py
├── activities/
│   ├── __init__.py
│   └── processing.py        # processor-driven activities live here
├── client.py                # helpers for starting Temporal client when needed
├── shared.py                # shared activity utilities (timeouts, logging hooks)
├── worker.py                # worker entry point (process hosting registered activities)
└── workflows.py             # workflow stubs / orchestrators (daily digest, etc.)
```

2. ✅ Added timeout/retry policy presets (FAST/MEDIUM/LONG_TIMEOUT, retry policies)
3. ✅ Added client helpers (get_temporal_client, start_workflow, query/cancel)
4. ✅ Added lightweight smoke tests (22 tests passing)

#### Phase 2: Relevance Activity Contract

3. Define the activity surface in `activities/processing.py` without implementation:
     - Function signature: `score_relevance_batch(profile_id: str, articles: list[Article], quality_scores: dict[str, int] | None = None) -> BatchRelevanceResult`
     - Returns `BatchRelevanceResult` containing original articles and relevance results keyed by article.url (preserves immutability)
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

**Phase 0-1 (Complete)**:

- ✅ Processor refactor complete: processors return new objects, no in-place mutations
- ✅ All 182 processor tests passing
- ✅ Documentation updated: `common_patterns.md`, `content_processing.md`, 4 processor docs
- ✅ Temporal scaffolding exists (`app/temporal/` package with shared helpers)
- ✅ TemporalSettings added to config.py with server_url, namespace, task_queue
- ✅ Activity options presets (FAST/MEDIUM/LONG_TIMEOUT, retry policies) in shared.py
- ✅ Client helpers (get_temporal_client, start_workflow, query/cancel) in client.py
- ✅ Activity stub `score_relevance_batch` exists in `app/temporal/activities/processing.py` with BatchRelevanceResult
- ✅ 22 tests passing: import smoke tests + shared utility unit tests

**Phase 1.5 (Complete)**:

- ✅ Activity has `@activity.defn` decorator with timeout/retry (app/temporal/activities/processing.py:42-45)
- ✅ Worker implementation exists (`app/temporal/worker.py` - 93 lines)
- ✅ Client uses singleton pattern with proper shutdown (app/temporal/client.py with asyncio.Lock)
- ⚠️ Activities use class-based pattern with dependency injection (deferred to Phase 2)
- ✅ Domain exceptions defined (`app/exceptions.py` - 65 lines with RetryableError/NonRetryableError)
- ✅ URL normalization utility (enhanced in app/processors/normalizer.py)
- ✅ Observability fields in `BatchRelevanceResult` (start/end timestamps, ai_calls, errors_count)
- ✅ Minimal workflow stub exists (app/temporal/workflows.py - 195 lines with complete TODO sequence)
- ✅ Serialization tested (tests/test_temporal/test_workflow_integration.py - 105 lines)

**Phase 2-3 (Ready to Start)**:

- ❌ Activity `score_relevance_batch` implementation
- ❌ Activity passes 6+ integration tests covering happy path, idempotency, errors
- ❌ Metadata fields flow correctly through pipeline orchestrator
- ❌ Idempotency verified: cache guard (`profile.id` + `article.url`) prevents redundant scoring
- ❌ Documentation updated in remaining places (`temporal-workflows.md`, `status_board.md`)

### Out of Scope (Tracked Separately)

- Digest assembly using relevance metadata (tracked as "Digest assembly enhancements")
- Quality scorer / summarizer caching (separate pending items)
- Metrics / telemetry (blocked pending sink selection)
