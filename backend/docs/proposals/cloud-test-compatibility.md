# Proposal: Cloud-Compatible Testing Without Docker

**Status**: Draft
**Created**: 2025-11-13
**Author**: Claude
**Problem**: Backend tests require Postgres Docker containers via `pytest-mock-resources`, which cannot run in Claude Code cloud environment

---

## Executive Summary

Our current test infrastructure uses `pytest-mock-resources` to spawn PostgreSQL Docker containers dynamically. This approach is incompatible with cloud development environments like Claude Code where Docker is unavailable. This proposal outlines multiple strategies to enable test execution in cloud environments while maintaining test quality and preserving the local development experience.

**Recommended Approach**: Hybrid fixture system with environment-based test selection (Option 4)

---

## Current State Analysis

### What We Have

**Test Distribution** (from exploration):
- **Unit Tests**: ~80% of test suite, processor tests with full mocking
- **Integration Tests**: ~15%, requires real Postgres (`test_processors/test_integration.py`)
- **Temporal Activity Tests**: ~5%, requires real Postgres for DB operations (`test_temporal/test_activities_*.py`)

### Critical Dependencies

```toml
# From backend/pyproject.toml
[dependency-groups]
dev = [
    "pytest-mock-resources>=2.12.4",  # Spawns Postgres Docker containers
    "pytest-xdist>=3.8.0",            # Parallel execution (6432 + worker offset)
    "python-on-whales>=0.78.0",       # Docker Python client
]
```

### Postgres Usage Pattern

**From `backend/tests/conftest.py`**:
```python
# Lines 59-72: Container configuration
postgress = create_postgres_fixture(scope="session", async_=True)

@pytest.fixture(scope="session")
def pmr_postgres_config(worker_id):
    return PostgresConfig(
        image="pgvector/pgvector:pg17",    # Requires Docker
        port=6432 + (0 if worker_id == "master" else int(worker_id[2:])),
        # ... other config
    )

# Lines 101-120: Schema management per test
@pytest.fixture(autouse=True)
def setup_database(override_environment, postgress):
    engine = create_engine(...)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)  # Fresh schema per test
    yield
    SQLModel.metadata.drop_all(engine)
```

### What Breaks in Cloud

1. **Docker unavailable** → `pytest-mock-resources` cannot spawn containers
2. **Test failures cascade** → Integration tests + Temporal activity tests fail
3. **CI/CD blocked** → Cannot run tests in cloud-based agents
4. **Development friction** → Cloud-only developers cannot run full test suite

---

## Solution Options

### Option 1: SQLite In-Memory Database (Simple, Lossy)

**Approach**: Replace Postgres with SQLite in-memory database for cloud environments

**Implementation**:
```python
# backend/tests/conftest.py
import os

@pytest.fixture(scope="session")
def database_url():
    if os.getenv("CLOUD_ENVIRONMENT"):
        return "sqlite+aiosqlite:///:memory:"  # Cloud
    else:
        # Use pytest-mock-resources Postgres (local)
        return get_pmr_postgres_url()
```

**Pros**:
- ✅ No external dependencies
- ✅ Fast test execution
- ✅ Works everywhere (cloud + local)
- ✅ Minimal code changes

**Cons**:
- ❌ **Loses pgvector testing** - No vector similarity testing
- ❌ **SQL dialect differences** - Postgres-specific features untested
- ❌ **False positives** - Tests pass with SQLite but fail in production
- ❌ **Schema differences** - JSON columns, array types behave differently
- ❌ **Async support** - `aiosqlite` has different transaction semantics

**Verdict**: ❌ **Not recommended** - Too many compromises for a Postgres-centric app

---

### Option 2: Skip Integration Tests in Cloud (Conservative)

**Approach**: Use pytest markers to skip Postgres-dependent tests in cloud environments

**Implementation**:
```python
# backend/tests/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "requires_postgres: mark test as requiring Postgres")

@pytest.fixture(autouse=True)
def skip_if_no_postgres(request):
    if request.node.get_closest_marker("requires_postgres"):
        if os.getenv("CLOUD_ENVIRONMENT"):
            pytest.skip("Postgres not available in cloud environment")

# Usage in tests
@pytest.mark.requires_postgres
async def test_fetch_user_config_success(...):
    # Test skipped in cloud, runs locally
    pass
```

**Marking Strategy**:
```bash
# Mark integration tests
@pytest.mark.requires_postgres  # test_processors/test_integration.py
@pytest.mark.requires_postgres  # test_temporal/test_activities_content.py
@pytest.mark.requires_postgres  # test_temporal/test_activities_processing.py
```

**Pros**:
- ✅ Simple implementation (~20 lines)
- ✅ No test quality degradation
- ✅ Clear separation of concerns
- ✅ Local development unchanged

**Cons**:
- ❌ **Reduced cloud coverage** - ~20% of tests skipped
- ❌ **Hidden bugs** - DB integration issues not caught in cloud
- ❌ **False confidence** - Green checkmark but incomplete testing

**Verdict**: ⚠️ **Acceptable short-term** - Good for immediate unblocking, but not a long-term solution

---

### Option 3: Mock Database Layer Aggressively (High Effort)

**Approach**: Create comprehensive mocks for all database operations

**Implementation**:
```python
# backend/tests/mocks/database.py
class MockAsyncSession:
    def __init__(self):
        self._data = {}

    async def execute(self, stmt):
        # Parse SQLAlchemy statement and return mock results
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

@pytest.fixture
def mock_db_session():
    return MockAsyncSession()

# Usage
async def test_fetch_user_config(mock_db_session):
    # Replace get_async_session dependency
    activity = ContentActivities()
    result = await activity.fetch_user_config(...)
```

**Pros**:
- ✅ Full cloud compatibility
- ✅ Fast test execution
- ✅ No external dependencies

**Cons**:
- ❌ **High maintenance** - Mock must mirror SQLAlchemy behavior
- ❌ **Test drift** - Mocks diverge from real DB over time
- ❌ **False positives** - Mock behaves differently than Postgres
- ❌ **Large refactor** - Requires rewriting ~15% of tests

**Verdict**: ❌ **Not recommended** - High cost, high risk of test rot

---

### Option 4: Hybrid Fixture System (Recommended)

**Approach**: Environment-aware fixtures that adapt to execution context

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│                   Test Execution                    │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    Local Dev                      Cloud Environment
    (Docker available)             (No Docker)
         │                               │
    ┌────▼────┐                     ┌────▼────┐
    │ Postgres│                     │ In-Mem  │
    │ Docker  │                     │ SQLModel│
    │ (real)  │                     │ (mock)  │
    └─────────┘                     └─────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                ┌────────▼─────────┐
                │ Test Layer Split │
                └──────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐   ┌────▼──────┐  ┌─────▼──────┐
    │Unit Tests│   │Integration│  │ Temporal   │
    │(no DB)   │   │(DB needed)│  │ Activities │
    └──────────┘   └───────────┘  └────────────┘
         │               │               │
         │          (local only)    (local only)
         │          or (degraded)   or (degraded)
         │
    All Envs
```

**Implementation Plan**:

#### Phase 1: Environment Detection
```python
# backend/tests/conftest.py
import os
import shutil

def is_docker_available() -> bool:
    """Check if Docker is available and running."""
    return shutil.which("docker") is not None

def is_cloud_environment() -> bool:
    """Detect if running in cloud environment."""
    return (
        os.getenv("CLAUDE_CODE_CLOUD") == "true" or
        os.getenv("CI_CLOUD_ENV") == "true" or
        not is_docker_available()
    )

@pytest.fixture(scope="session")
def test_environment() -> str:
    """Returns 'local' or 'cloud'."""
    return "cloud" if is_cloud_environment() else "local"
```

#### Phase 2: Adaptive Database Fixture
```python
# backend/tests/conftest.py

# Local: pytest-mock-resources (existing)
postgress = create_postgres_fixture(scope="session", async_=True)

@pytest.fixture(scope="session")
def pmr_postgres_config(worker_id):
    # Existing configuration
    return PostgresConfig(image="pgvector/pgvector:pg17", ...)

# Cloud: In-memory data structures
class InMemoryDataStore:
    """Minimal in-memory storage for cloud testing."""
    def __init__(self):
        self.users = {}
        self.sources = {}
        self.configs = {}
        self.interest_profiles = {}

    def clear(self):
        self.users.clear()
        self.sources.clear()
        self.configs.clear()
        self.interest_profiles.clear()

@pytest.fixture(scope="session")
def in_memory_store():
    store = InMemoryDataStore()
    yield store
    store.clear()

# Adaptive fixture
@pytest.fixture(scope="session")
def database_url(test_environment, pmr_postgres_config, in_memory_store):
    if test_environment == "local":
        # Use Postgres Docker
        database_url = "{0.drivername}://{0.username}:{0.password}@{0.host}:{0.port}/{0.root_database}"
        return database_url.format(pmr_postgres_config)
    else:
        # Cloud: Signal to use in-memory mocks
        return "mock://in-memory"
```

#### Phase 3: Test Layer Strategy

**Unit Tests** (80% - `test_processors/test_*_*.py`):
- Status: ✅ Already cloud-compatible
- No changes needed (all mocked)

**Integration Tests** (15% - `test_processors/test_integration.py`):
- **Local**: Run against real Postgres
- **Cloud**: Two sub-options:
  - **A) Skip** (conservative): Mark with `@pytest.mark.requires_postgres`
  - **B) Degrade gracefully** (progressive): Run with in-memory mocks + warning

**Temporal Activity Tests** (5% - `test_temporal/test_activities_*.py`):
- **Local**: Run against real Postgres
- **Cloud**: Two sub-options:
  - **A) Skip** (conservative)
  - **B) Mock repository layer** (more work)

#### Phase 4: Test Markers & Selective Execution
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "requires_postgres: Test requires real PostgreSQL database",
    "cloud_compatible: Test runs in cloud without Postgres",
]

# Automatic skipping in cloud
def pytest_configure(config):
    config.addinivalue_line("markers", "requires_postgres: Requires PostgreSQL")

@pytest.fixture(autouse=True)
def skip_postgres_tests_in_cloud(request, test_environment):
    if request.node.get_closest_marker("requires_postgres"):
        if test_environment == "cloud":
            pytest.skip("PostgreSQL not available in cloud environment")
```

**Marking Examples**:
```python
# Integration test - skip in cloud
@pytest.mark.requires_postgres
def test_end_to_end_digest_pipeline():
    pass

# Unit test - runs everywhere
@pytest.mark.cloud_compatible
def test_quality_scorer_weights():
    pass
```

#### Phase 5: Cloud Feedback & Transparency
```python
# Generate test report showing skipped tests
def pytest_sessionfinish(session, exitstatus):
    if is_cloud_environment():
        skipped = [item for item in session.items if item.get_closest_marker("requires_postgres")]
        if skipped:
            logger.warning(
                f"⚠️  Cloud Environment: {len(skipped)} Postgres-dependent tests skipped\n"
                f"   Run locally with Docker for full coverage"
            )
```

**Pros**:
- ✅ **Local dev unchanged** - Developers keep full Postgres testing
- ✅ **Cloud unblocked** - Unit tests (80%) run immediately
- ✅ **Clear visibility** - Test reports show what's skipped
- ✅ **Progressive enhancement** - Can add degraded testing later
- ✅ **Low risk** - No test quality degradation for local dev

**Cons**:
- ⚠️ **Partial cloud coverage** - Integration tests skipped (15-20%)
- ⚠️ **Dual maintenance** - Need to keep both paths working

**Verdict**: ✅ **Recommended** - Best balance of effort, risk, and compatibility

---

### Option 5: Hosted Test Database (Enterprise)

**Approach**: Use cloud-hosted Postgres for tests (e.g., Neon, Supabase, Railway)

**Implementation**:
```python
# backend/tests/conftest.py
@pytest.fixture(scope="session")
def database_url(test_environment):
    if test_environment == "cloud":
        # Use hosted test database
        return os.environ["CLOUD_TEST_DATABASE_URL"]  # e.g., Neon serverless Postgres
    else:
        # Local: pytest-mock-resources
        return get_pmr_postgres_url()
```

**Pros**:
- ✅ **Real Postgres** - Full feature parity with production
- ✅ **pgvector support** - Can test similarity detection
- ✅ **No Docker needed** - Connection string only

**Cons**:
- ❌ **Cost** - Monthly fees for hosted DB (even if ephemeral)
- ❌ **Network latency** - Slower than local containers
- ❌ **Credentials management** - Need secure env var injection
- ❌ **Cleanup complexity** - Must drop/recreate schemas per test run
- ❌ **Parallel execution** - Hard to isolate concurrent test runs

**Verdict**: ⚠️ **Consider for CI/CD** - Good for GitHub Actions, overkill for interactive cloud dev

---

## Recommended Implementation Plan

### Phase 1: Immediate Unblocking (Week 1)

**Goal**: Enable unit tests in cloud environments

**Tasks**:
1. ✅ Add environment detection functions
2. ✅ Add pytest markers (`requires_postgres`, `cloud_compatible`)
3. ✅ Mark integration tests with `@pytest.mark.requires_postgres`
4. ✅ Configure pytest to skip marked tests in cloud
5. ✅ Add test report warning for skipped tests

**Files to modify**:
- `backend/tests/conftest.py` (~50 lines)
- `backend/tests/test_processors/test_integration.py` (add marker)
- `backend/tests/test_temporal/test_activities_content.py` (add marker)
- `backend/tests/test_temporal/test_activities_processing.py` (add marker)
- `backend/pyproject.toml` (add pytest markers config)

**Expected Outcome**:
- Unit tests (80%) run in cloud ✅
- Integration tests (20%) skipped in cloud ⚠️
- Local development unchanged ✅

### Phase 2: Documentation & Developer Experience (Week 2)

**Goal**: Clear communication about test coverage differences

**Tasks**:
1. ✅ Update `backend/docs/testing-strategy.md` with cloud testing section
2. ✅ Add `backend/docs/cloud-development.md` guide
3. ✅ Update `README.md` with test execution instructions
4. ✅ Add pre-commit hook to validate test markers

**Expected Outcome**:
- Developers understand why tests are skipped
- Clear instructions for running full suite locally
- Automated validation of test categorization

### Phase 3: Progressive Enhancement (Future)

**Goal**: Increase cloud test coverage without compromising quality

**Tasks** (prioritize based on feedback):
1. Mock repository layer for Temporal activity tests
2. Add degraded integration tests with in-memory data
3. Evaluate hosted test database for CI/CD pipelines
4. Implement SQLite for read-only integration tests

**Expected Outcome**:
- Cloud coverage increases from 80% → 90%
- Maintain high-confidence local testing
- Reduce false positives from mocking

---

## Implementation Example

### File: `backend/tests/conftest.py` (additions)

```python
import os
import shutil
import pytest

# ============================================================================
# Environment Detection
# ============================================================================

def is_docker_available() -> bool:
    """Check if Docker CLI is available."""
    return shutil.which("docker") is not None

def is_cloud_environment() -> bool:
    """Detect if running in cloud environment without Docker."""
    return (
        os.getenv("CLAUDE_CODE_CLOUD") == "true" or
        os.getenv("CI_CLOUD_ENV") == "true" or
        not is_docker_available()
    )

@pytest.fixture(scope="session")
def test_environment() -> str:
    """Returns 'local' or 'cloud' based on environment detection."""
    env = "cloud" if is_cloud_environment() else "local"
    logger.info(f"Test environment detected: {env}")
    return env

# ============================================================================
# Conditional Test Skipping
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_postgres: mark test as requiring real PostgreSQL database"
    )
    config.addinivalue_line(
        "markers",
        "cloud_compatible: mark test as runnable in cloud without Postgres"
    )

@pytest.fixture(autouse=True)
def skip_postgres_tests_in_cloud(request, test_environment):
    """Automatically skip Postgres-dependent tests in cloud environments."""
    if request.node.get_closest_marker("requires_postgres"):
        if test_environment == "cloud":
            pytest.skip("PostgreSQL not available in cloud environment")

# ============================================================================
# Existing Fixtures (unchanged in Phase 1)
# ============================================================================

# Keep existing: cleanup_docker_containers, pmr_postgres_config,
# database_url, override_environment, setup_database, etc.
# These continue to work in local environments
```

### File: `backend/tests/test_temporal/test_activities_content.py` (marking)

```python
import pytest

@pytest.mark.requires_postgres  # ← Add this marker
@pytest.mark.asyncio
async def test_fetch_user_config_success(
    clear_async_db_cache,
    test_user: User,
    test_digest_config: DigestConfiguration,
    test_sources: list[ContentSource],
    test_interest_profile: InterestProfile,
):
    """Test successful user configuration fetch from database."""
    activity = ContentActivities()
    result = await activity.fetch_user_config(
        sc.FetchUserConfigRequest(user_id=test_user.id)
    )
    assert result.user_config.user_id == test_user.id
```

### File: `backend/pyproject.toml` (configuration)

```toml
[tool.pytest.ini_options]
markers = [
    "requires_postgres: Test requires real PostgreSQL database (local only)",
    "cloud_compatible: Test runs in cloud without Postgres",
]

# Optional: Add reporting plugin
addopts = [
    "-v",
    "--strict-markers",
    # Show skipped tests with reasons
    "-ra",
]
```

---

## Testing the Implementation

### Verify Local Environment (should work unchanged)
```bash
cd backend
uv run pytest tests/ -v
# Expected: All tests run, ~100% pass
```

### Simulate Cloud Environment
```bash
export CLAUDE_CODE_CLOUD=true
uv run pytest tests/ -v
# Expected:
#   - Unit tests: PASS (green)
#   - Integration tests: SKIPPED (yellow) with reason
#   - Final warning: "20 tests skipped - run locally for full coverage"
```

### Check Markers
```bash
uv run pytest tests/ --markers
# Expected: See requires_postgres and cloud_compatible markers listed
```

---

## Success Metrics

### Phase 1 Success Criteria
- ✅ 80% of tests run successfully in cloud environment
- ✅ 0% false positives (tests that pass in cloud but fail locally)
- ✅ Local development workflow unchanged
- ✅ Clear test reports showing skipped tests with reasons
- ✅ Documentation updated with cloud testing guidelines

### Long-term Goals (Phase 3+)
- 🎯 90% test coverage in cloud environments
- 🎯 <5% test maintenance overhead for dual-environment support
- 🎯 Zero developer confusion about test skipping

---

## Migration Checklist

### Prerequisites
- [ ] Review current test dependencies in `pyproject.toml`
- [ ] Audit all tests to identify Postgres dependencies
- [ ] Communicate changes to development team

### Phase 1 Implementation
- [ ] Add environment detection functions to `conftest.py`
- [ ] Register pytest markers in `pyproject.toml`
- [ ] Add `@pytest.mark.requires_postgres` to integration tests
- [ ] Add `@pytest.mark.requires_postgres` to Temporal activity tests
- [ ] Implement auto-skip fixture
- [ ] Add test session warning for skipped tests
- [ ] Test locally: `uv run pytest tests/`
- [ ] Test cloud simulation: `CLAUDE_CODE_CLOUD=true uv run pytest tests/`

### Documentation
- [ ] Update `backend/docs/testing-strategy.md`
- [ ] Create `backend/docs/cloud-development.md`
- [ ] Update root `README.md` with test instructions
- [ ] Add inline comments explaining marker usage

### Validation
- [ ] Run full test suite locally (should pass 100%)
- [ ] Run simulated cloud tests (should skip 20%, pass 80%)
- [ ] Verify no false positives (no tests pass in cloud but fail locally)
- [ ] Review test report output for clarity

---

## Alternative Considerations

### Why Not [X]?

**Q: Why not just use SQLite for everything?**
A: Postgres-specific features (pgvector, array types, JSON operators) would be untested. False confidence is worse than explicit skipping.

**Q: Why not mock all database operations?**
A: High maintenance burden. Mocks drift from reality. Integration tests exist to catch real DB issues.

**Q: Why not use a hosted Postgres for cloud tests?**
A: Cost, latency, and credential management complexity. Good for CI/CD, overkill for interactive development.

**Q: Why not run Docker-in-Docker in cloud?**
A: Security, performance, and reliability issues. Most cloud dev environments explicitly block DinD.

---

## Appendix: Test Categorization Audit

### Tests That Don't Need Postgres (Cloud-Compatible)

**`test_processors/`** (Unit Tests - Already Mocked):
- ✅ `test_ai_summarizer.py` - Mocks AI provider
- ✅ `test_cache_manager.py` - Uses FakeAsyncRedis
- ✅ `test_content_fetcher.py` - Mocks HTTP client
- ✅ `test_deduplicator.py` - Pure logic
- ✅ `test_interest_matcher.py` - Pure logic
- ✅ `test_quality_scorer.py` - Pure logic
- ✅ `test_similarity_detector.py` - Pure logic
- ✅ All other processor tests (~20 files)

**`test_utils/`**:
- ✅ `test_cache_utils.py` - Uses FakeAsyncRedis
- ✅ `test_text_processing.py` - Pure logic
- ✅ `test_url_validation.py` - Mocks HTTP

**`test_temporal/`** (Workflow Tests - Already Mocked):
- ✅ `test_workflow_integration.py` - Uses mocked activities

### Tests That Require Postgres (Mark for Skipping)

**`test_processors/`**:
- ❌ `test_integration.py` - End-to-end pipeline with DB

**`test_temporal/`**:
- ❌ `test_activities_content.py` - DB queries via SQLModel
- ❌ `test_activities_processing.py` - DB writes via repositories

**`test_main.py`** (Mixed):
- ✅ `/health` endpoint - No DB (mock Temporal only)
- ❌ `/auth/*` endpoints - Requires users table
- ❌ `/digest/*` endpoints - Requires full DB schema

**Total**: ~12-15 test files need marking (~20% of suite)

---

## Questions & Feedback

**For Discussion**:
1. Should we prioritize Phase 3 (progressive enhancement) or is 80% coverage acceptable?
2. Do we want degraded integration tests (with mocks) or clean skips?
3. Should we add a hosted test DB for CI/CD pipelines?
4. What's the acceptable coverage gap for cloud vs local?

**Contact**: Review with team before implementing Phase 1

---

**End of Proposal**
