# Personalization Pipeline Integration Plan

## Summary

Refactor processors so they stop mutating articles in-place, then stand up the missing Temporal scaffolding and wire the existing `RelevanceScorer` into a batch activity with a sane idempotency contract plus end‑to‑end metadata validation.

## Current State

### ✅ Phase 0 Complete: Processor Refactor (2025-10-12)

### ✅ Phase 1 Complete: Temporal Infrastructure (2025-10-12)

### ✅ Phase 1.5 Complete: Critical Integration Fixes (2025-10-12)

**Status**: All blocking issues resolved. Infrastructure ready for Phase 2 implementation.

**Next**: Phase 4 - Integration Verification (end-to-end chain) – subsequent workflow orchestration phases remain pending.

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

#### Phase 2: Relevance Activity Contract (Complete)

Implemented as specified:

- `score_relevance_batch` signature finalized (uses `BatchRelevanceRequest` wrapper instead of loose params)
- Returns immutable `BatchRelevanceResult` holding original articles + relevance map
- Idempotency: cache key `relevance:{profile_hash}:{article_url}` where profile hash derives from keywords, threshold, boost_factor
- Timeout / retry policy documented in `temporal-workflows.md` (Medium class) and enforced via decorator usage in worker registration (policy wiring pending explicit constants integration)
- Validation errors raise `ValidationError`; other exceptions captured per-article for partial continuation

#### Phase 3: Activity Implementation & Tests (Complete)

Delivered capabilities:

- Full implementation present in `app/temporal/activities/processing.py`
- Dependency wiring: pulls settings, redis client, async session + repository, ai provider factory
- Caching: Redis `setex` with TTL from personalization settings; cache hits short‑circuit scoring loop
- Observability fields populated: `start_timestamp`, `end_timestamp`, `ai_calls`, `cache_hits`, `errors_count`
- Partial failure handling: per-article try/except; failed articles omitted from `relevance_results` while loop continues
- Tests in `tests/test_temporal/test_activities_processing.py` cover:
  - Cache key determinism & variation
  - Happy path scoring with quality score inputs
  - Idempotency (second invocation all cache hits)
  - Empty profile behavior (threshold pass with zero score)
  - AI failure fallback (semantic score 0, no counted error)
  - Partial per-article failure (errors_count increment)
  - Explicit cache behavior (miss then hit)

Remaining gaps (deferred to later phases):

- No quality/topic/summarizer batch activities yet (placeholders only in workflow doc)
- AI call counting heuristic (semantic_score > 0) may undercount deterministic AI paths; refine once telemetry sink chosen
- Retry policy currently implicit; needs centralized constants applied when more activities added

#### Phase 4: Integration Verification (In Progress / Pending Upstream Activities)

Blocked prerequisites:

- Missing implemented activities for normalization, quality scoring, topic extraction to form full chain
- Workflow (`DailyDigestWorkflow`) still uses TODO placeholders and executes a minimal relevance activity call with empty inputs

Planned tasks to complete Phase 4 once upstream activities land:

 1. Implement normalization, quality, topic (and optionally summarization) activities with same immutability + caching conventions
 2. Add end-to-end test constructing a synthetic profile + articles executing: normalize → quality → topics → relevance
 3. Assert metadata propagation (`quality_score`, `ai_topics`, `relevance_score`, `passes_threshold`)
 4. Add cache warm test: first run populates, second run asserts cache_hits equals article count and zero AI calls
 5. Extend `temporal-workflows.md` matrix with new activities (mark ✅ as they land)

#### Phase 5: Workflow Integration (Not Started)

8. Expand `DailyDigestWorkflow` from placeholders to real activity invocations:
     - Replace TODO blocks with `workflow.execute_activity` calls referencing implemented batch activities
     - Introduce structured aggregation of per-activity observability (sum AI calls, accumulate errors)
     - Implement relevance phase using real articles rather than empty list once earlier phases exist
9. Add email assembly + send + delivery record activities (scoped for later milestone, optional for MVP if digest generation validated separately)

#### Phase 6: Documentation Updates

9. Toggle `docs/temporal-workflows.md` activity rows from “planned” to “implemented” as each new activity ships (normalizer, quality, topics, summarizer, etc.).
10. Update `docs/processors/content_processing.md` and `docs/processors/relevance_scorer.md` with cross-links once end-to-end chain validated (add section on batch activity interfaces & cache strategy).
11. Update `backend/docs/plan_status/status_board.md` when Phase 4 turns green (end-to-end metadata test passing) and again after workflow orchestration moves to Phase 5.

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

**Phase 2-3 (Complete - 2025-10-14)**:

- ✅ Activity `score_relevance_batch` implementation (see `app/temporal/activities/processing.py`)
- ✅ ProfileRepository for profile lookups (`app/repositories/profile_repository.py`)
- ✅ Cache key hashing: SHA256 of sorted profile keywords + threshold + boost_factor + article URL
- ✅ Test suite: coverage for idempotency, cache behavior, AI fallback, partial failure (`tests/test_temporal/test_activities_processing.py`)
- ✅ Graceful per-article error handling & metrics (`errors_count`, `cache_hits`, `ai_calls`, timestamps)
- ✅ `temporal-workflows.md` updated (activity row marked ✅)
- ⚠️ Only relevance batch activity implemented; other planned activities remain in 'planned' state
- ⚠️ Workflow orchestrator still placeholder (does not execute full pipeline yet)

### Out of Scope (Tracked Separately)

- Digest assembly using relevance metadata (tracked as "Digest assembly enhancements")
- Quality scorer / summarizer caching (separate pending items)
- Metrics / telemetry (blocked pending sink selection)
