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

## Test Client Selection (Sync vs Async)

### Use `client` (Sync TestClient)

Use the sync `client` fixture when:
- Test does NOT use database fixtures (like `test_user`, `session`)
- OR endpoint does validation only without database access
- OR test creates data through API calls (not fixtures)

```python
def test_register_user_success(client: TestClient):
    # No fixtures, creates user via API
    response = client.post("/users/auth/register", json={...})
    assert response.status_code == 201
```

**Examples:**
- `test_register_user_success` - Creates user via API
- `test_register_user_short_password` - Validation only
- `test_get_user_profile_unauthenticated` - No database query

### Use `async_client` (Async HTTP Client)

Use the async `async_client` fixture when:
- Test uses database fixtures (like `test_user`, `session`) to create test data
- AND API endpoint accesses the database (queries, updates)
- MUST combine with `clear_async_db_cache` fixture

```python
@pytest.mark.asyncio
async def test_login_success(async_client, clear_async_db_cache, test_user: User):
    # Uses test_user fixture + endpoint queries database
    response = await async_client.post("/users/auth/login", json={...})
    assert response.status_code == 200
```

**Examples:**
- `test_login_success` - Uses test_user fixture + queries database
- `test_update_user_profile_timezone` - Uses test_user + updates database
- `test_get_digest_config_success` - Uses test_user + queries config

### Why This Matters

**The Problem:**
- Sync fixtures (via `session`) and async endpoints share connection pools
- Without proper isolation, PostgreSQL throws "another operation is in progress" errors
- `clear_async_db_cache` forces async code to create fresh database connections

**The Rule:**
- Database fixtures + database-accessing endpoints = `async_client` + `clear_async_db_cache`
- Everything else = `client` (simpler, faster)

**Pattern Template:**
```python
# Async pattern (when using DB fixtures)
@pytest.mark.asyncio
async def test_something(async_client, clear_async_db_cache, test_user):
    response = await async_client.post("/endpoint", json={...})
    assert response.status_code == 200

# Sync pattern (when not using DB fixtures)
def test_something(client: TestClient):
    response = client.post("/endpoint", json={...})
    assert response.status_code == 200
```

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
