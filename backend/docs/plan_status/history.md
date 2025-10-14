# Backend Workstream History

## 2025-10-14

### Code Quality Improvements

- Removed auto-commit from `get_async_session()` to give callers explicit transaction control.
- Deleted unused `initial_ai_count` variable from batch relevance scoring activity.
- Stripped verbose docstrings from `ProfileRepository` (type hints + clear names = self-documenting).
- Documented SQLModel forward reference limitation: must use `Optional["Class"]` instead of `"Class" | None` for Relationship fields.

### Documentation Updates

- Updated `docs/design-patterns.md` Section 3 (Session Management) to document explicit commit pattern.
- Added `docs/design-patterns.md` Section 4 (Type Annotations & SQLModel Constraints) with technical explanation and examples.
- 258 tests passing, all changes non-breaking.

### Key File Changes

- Modified: `app/database.py` (removed auto-commit), `app/temporal/activities/processing.py` (cleanup), `app/repositories/profile_repository.py` (docstring reduction), `docs/design-patterns.md` (technical constraints).

## 2025-10-12

### Processor Refactor

- 6 processors now return immutable result models (`ContentQualityResult`, `RelevanceResult`, `SummaryResult`).
- Normalizer uses `model_copy(update=...)`; explicit dependency passing (quality score → relevance, topics → summarizer).
- 182 tests updated; immutability documented.

### Temporal Foundations

- Added `app/temporal/` layout, timeout/retry presets.

### Integration Hardening (Phase 1.5)

- Added activity decorator + policies; singleton Temporal client (race-safe).
- Worker entry point (separate service) with graceful shutdown.
- Workflow stub (typed I/O) + serialization integration test (Articles + InterestProfile).

### Design / Observability

- Domain exceptions: retryable vs non-retryable.
- In-place URL normalization improvements (strip tracking, sort query, normalize, drop fragments).
- Added batch relevance observability (timestamps, ai_calls, errors_count).

### Key File Changes

- New: `app/exceptions.py`, `app/temporal/worker.py`, `app/temporal/workflows.py`, workflow integration test.
- Modified: Temporal client (singleton), shared constants, processing activity (decorated + metrics), normalizer (URL), main (startup/shutdown), `docker-compose.yml` (worker service).

### Outstanding Debt

- Redis shutdown impact (Phase 4).

## 2025-10-10

- RSS fetch layer (73 tests).
- AI provider abstraction (Gemini live, OpenAI stub).
- Similarity, topic extraction, normalization (≈170 processor tests total).
- Quality + relevance scoring merged; personalization fields + `RelevanceScorer` (commit 71e1c87); docs moved under `docs/processors/`.

## 2025-09-28

- Core FastAPI scaffolding, DB models, Redis cache utilities stabilized (Phase 1 MVP baseline).
