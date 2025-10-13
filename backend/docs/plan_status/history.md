# Backend Workstream History

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
