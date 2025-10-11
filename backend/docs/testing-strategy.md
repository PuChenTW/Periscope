# Testing Strategy

## Test Pyramid

| Layer | Location | Goal | Notes |
| --- | --- | --- | --- |
| Unit | `tests/unit/` | Validate single function/module with fakes. | No I/O; mock AI providers + Redis. |
| Integration | `tests/integration/` | Exercise API + DB flow. | Use test Postgres/Redis via fixtures; assert HTTP + persistence. |
| Temporal | `tests/temporal/` | Verify workflow orchestration + retries. | Temporal test harness; mock slow/external activities. |

## Ground Rules

- Every new processor gets unit tests covering success + failure/fallback paths.
- External services (RSS, AI, email) are mocked; never hit real endpoints.
- Use fixtures under `tests/fixtures/` for shared setup (DB, sample articles, fake AI responses).
- Keep unit tests <10 ms; integration <1 s; fail builds if thresholds drift.

## What to Test

| Area | Must Cover |
| --- | --- |
| API endpoints | Auth, validation errors, happy path response, DB state change. |
| Processors | Inputs → outputs, cache hits/misses, error fallback behaviour. |
| Repositories | Query correctness, pagination, constraint handling. |
| Temporal workflows | Activity order, retry policy, partial failure paths, signals. |

## Tooling

- Use `uv run pytest` (never bare `pytest`).
- `pytest-mock` for mocks; `responses` for HTTP stubbing.
- `pytest-mock-resources` for Postgres if running integration tests in parallel.
- Coverage tracked via `uv run pytest --cov`; target ≥85% on processors and workflows.

## Adding Tests Checklist

- [ ] Place file under correct layer directory.
- [ ] Import shared fixtures instead of duplicating builders.
- [ ] Name test `test_<behavior>`; follow Arrange/Act/Assert.
- [ ] Assert invariants, not implementation details.
- [ ] Update CI command (if new mark/flag required).

## Debugging Failures

- Re-run failing test with `-vv` for assertion introspection.
- For Temporal tests, enable `TemporalTestEnvironment` logging to see replay history.
- Cache-related flake? ensure fixtures call `redis.flushdb()` before each test.

Keep it lean. Redundant tests slow us down—if a behaviour is covered at integration level, do not duplicate the same scenario at unit level without added value.
