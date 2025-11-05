# Test Coverage Enhancement Plan - Phase 4

## Executive Summary

**Current State**: Test coverage dropped from 85% to 42% overall (81% badge may be outdated)

**Root Causes**:
1. New code added in Phase 4 without corresponding tests
2. Existing integration tests require Docker infrastructure (not running in all environments)
3. Missing unit tests for new activities: `validate_and_filter_batch`, `score_quality_batch`, `extract_topics_batch`
4. Validation logic split from normalizer but tests not updated accordingly

**Goal**: Achieve 85%+ test coverage with balanced unit and integration test mix

---

## Coverage Analysis

### Critical Gaps (Priority 1)

| Module | Current Coverage | Missing Coverage | Impact |
|--------|-----------------|------------------|---------|
| `app/temporal/activities/processing.py` | 18% (154/187 lines) | All 5 batch activities | **CRITICAL** - Core workflow logic |
| `app/processors/validator.py` | 39% (34/56 lines) | Spam detection paths, error handling | **HIGH** - New validation logic |
| `app/temporal/worker.py` | 0% (40/40 lines) | Worker initialization, activity registration | **HIGH** - Runtime entry point |
| `app/temporal/workflows.py` | 42% (37/64 lines) | Workflow execution paths | **HIGH** - Orchestration logic |

### Secondary Gaps (Priority 2)

| Module | Current Coverage | Missing Coverage | Impact |
|--------|-----------------|------------------|---------|
| `app/temporal/client.py` | 21% (53/67 lines) | Client management, workflow operations | **MEDIUM** - API surface |
| `app/repositories/profile_repository.py` | 50% (7/14 lines) | Repository operations | **MEDIUM** - Data access |
| `app/utils/cache.py` | 31% (85/123 lines) | Cache utilities | **LOW** - Shared utilities |
| `app/utils/text_processing.py` | 14% (19/22 lines) | Text processing helpers | **LOW** - Utility functions |

---

## Implementation Plan

### Phase 1: Unit Tests for New Activities (Week 1)

**Objective**: Add isolated unit tests for the 3 missing batch activities

#### 1.1 Add Unit Tests for `validate_and_filter_batch`

**File**: `tests/test_temporal/test_activities_validation.py` (NEW)

**Test Cases** (12 tests):
- ✅ Happy path: all articles valid
- ✅ Mixed validation: some pass, some fail
- ✅ Empty content detection
- ✅ Minimum length enforcement
- ✅ Spam detection with cache hit
- ✅ Spam detection with cache miss
- ✅ AI spam detection enabled vs disabled
- ✅ Cache corruption handling (invalid JSON)
- ✅ Validation error handling (graceful failures)
- ✅ Empty article list
- ✅ ValidationResult serialization
- ✅ Cache key computation consistency

**Mocking Strategy**:
- Mock `ContentValidator` to avoid AI provider dependency
- Mock Redis client for cache operations
- Use pytest fixtures for sample articles

**Success Criteria**:
- All 12 tests passing
- Coverage for lines 52-142 in processing.py
- No Docker dependency

---

#### 1.2 Add Unit Tests for `score_quality_batch`

**File**: `tests/test_temporal/test_activities_quality.py` (NEW)

**Test Cases** (10 tests):
- ✅ Happy path: all articles scored successfully
- ✅ Quality scoring with cache hit
- ✅ Quality scoring with cache miss
- ✅ AI quality scoring enabled vs disabled
- ✅ Metadata-only scoring fallback (AI failure)
- ✅ Partial failure handling (some articles error)
- ✅ Empty article list
- ✅ Cache key computation consistency
- ✅ ContentQualityResult serialization
- ✅ Observability metrics (ai_calls, cache_hits, errors_count)

**Mocking Strategy**:
- Mock `QualityScorer.calculate_quality_score()`
- Mock Redis client for cache operations
- Use pytest fixtures for sample articles and quality results

**Success Criteria**:
- All 10 tests passing
- Coverage for lines 212-296 in processing.py
- No Docker dependency

---

#### 1.3 Add Unit Tests for `extract_topics_batch`

**File**: `tests/test_temporal/test_activities_topics.py` (NEW)

**Test Cases** (11 tests):
- ✅ Happy path: topics extracted successfully
- ✅ Topic extraction with cache hit
- ✅ Topic extraction with cache miss
- ✅ Empty topics result (no topics found)
- ✅ Partial failure handling (some articles error)
- ✅ Article mutation verification (ai_topics populated)
- ✅ Empty article list
- ✅ Cache key computation consistency
- ✅ Cache serialization (comma-separated topics)
- ✅ AI failure graceful handling (empty topics on error)
- ✅ Observability metrics (ai_calls, cache_hits, errors_count)

**Mocking Strategy**:
- Mock `TopicExtractor.extract_topics()`
- Mock Redis client for cache operations
- Use pytest fixtures for sample articles

**Success Criteria**:
- All 11 tests passing
- Coverage for lines 308-399 in processing.py
- No Docker dependency

---

### Phase 2: Update Existing Tests (Week 1)

**Objective**: Align existing tests with Phase 4 refactoring changes

#### 2.1 Update `test_normalizer.py`

**Changes Required**:
- ✅ Remove validation-related tests (moved to validator)
- ✅ Remove spam detection tests (moved to validator)
- ✅ Add tests for AI provider removal from normalizer
- ✅ Verify normalizer focuses only on metadata normalization
- ✅ Update test expectations (no filtering, no rejection)

**Expected Outcome**:
- Normalizer tests focus only on: URL normalization, date handling, title/author/tags cleanup
- ~50 lines removed (validation tests)
- ~30 lines added (metadata normalization edge cases)

---

#### 2.2 Update `test_activities_processing.py`

**Changes Required**:

**Existing Tests to Update**:
1. `test_normalize_articles_batch_spam_detection` → Move to validation activity tests
2. `test_normalize_articles_batch_ai_failure_graceful` → Move to validation activity tests
3. Update remaining normalize tests to remove validation expectations

**Expected Outcome**:
- Normalize activity tests focus only on normalization
- Validation tests moved to new validation activity test file
- Clear separation between validation and normalization testing

---

### Phase 3: Integration Tests (Week 2)

**Objective**: Add end-to-end integration tests that exercise the full pipeline

#### 3.1 End-to-End Activity Chain Test

**File**: `tests/test_temporal/test_activities_integration.py` (NEW)

**Test Cases** (5 tests):
- ✅ **Full pipeline**: validate → normalize → quality → topics → relevance
  - Start with raw articles
  - Verify data flows correctly through all 5 activities
  - Assert final relevance results are correct
  - Verify observability metrics accumulated correctly

- ✅ **Cache warm test**: Run pipeline twice, verify zero AI calls on second run
  - First run: cold cache (AI calls > 0)
  - Second run: warm cache (AI calls = 0)
  - Verify results identical between runs

- ✅ **Partial failure resilience**: Inject failures at each stage, verify graceful handling
  - Validation: some articles fail spam detection
  - Quality: some articles error during scoring
  - Topics: some articles fail extraction
  - Relevance: profile not found (should raise ValidationError)

- ✅ **Empty data flow**: Empty article list through entire pipeline
  - All activities should handle empty input gracefully
  - Verify observability metrics show zero processing

- ✅ **Large batch test**: Process 100 articles through pipeline
  - Verify batching efficiency
  - Check performance metrics (execution time)
  - Ensure no memory leaks or resource exhaustion

**Requirements**:
- **Requires Docker**: Postgres (for profile repo), Redis (for caching)
- Use `@pytest.mark.integration` decorator
- Use real dependencies (no mocking)

**Success Criteria**:
- All 5 integration tests passing
- Full pipeline coverage from raw articles to relevance scores
- Validates all activity interfaces work together

---

#### 3.2 Workflow Integration Tests

**File**: `tests/test_temporal/test_workflow_integration.py` (ENHANCE EXISTING)

**New Test Cases** (4 tests):
- ✅ **Workflow execution**: Run `DailyDigestWorkflow` end-to-end (with mocked fetch)
- ✅ **Error accumulation**: Verify errors tracked across all phases
- ✅ **AI call tracking**: Verify total_ai_calls aggregated correctly
- ✅ **Metrics validation**: Verify DigestWorkflowResult contains correct counts

**Requirements**:
- Mock source fetching (Phase 1 not implemented yet)
- Use real activities (integration test)
- Requires Docker

**Success Criteria**:
- Workflow executes all 5 processing phases
- Coverage for lines 99-237 in workflows.py
- Validates workflow orchestration logic

---

### Phase 4: Worker and Client Tests (Week 2)

**Objective**: Cover worker initialization and client management code

#### 4.1 Worker Tests

**File**: `tests/test_temporal/test_worker.py` (NEW)

**Test Cases** (6 tests):
- ✅ Worker initialization with correct settings
- ✅ Activity registration (all 5 activities registered)
- ✅ ProcessingActivities instance creation
- ✅ Worker task queue configuration
- ✅ Worker graceful shutdown
- ✅ Worker error handling (invalid settings)

**Mocking Strategy**:
- Mock Temporal connection
- Mock activity registration
- Use pytest fixtures for settings

**Success Criteria**:
- 100% coverage for worker.py (currently 0%)
- No Docker dependency (unit tests)

---

#### 4.2 Client Tests

**File**: `tests/test_temporal/test_client.py` (ENHANCE EXISTING)

**New Test Cases** (8 tests):
- ✅ Client singleton pattern verification
- ✅ Client initialization with settings
- ✅ Workflow start operation
- ✅ Workflow query operation
- ✅ Workflow cancel operation
- ✅ Client shutdown and cleanup
- ✅ Connection failure handling
- ✅ Concurrent client access (thread safety)

**Mocking Strategy**:
- Mock Temporal server connection
- Mock workflow handle operations

**Success Criteria**:
- Coverage increased from 21% to 85%+ for client.py

---

### Phase 5: Edge Cases and Error Paths (Week 3)

**Objective**: Cover remaining edge cases and error handling paths

#### 5.1 ContentValidator Edge Cases

**File**: `tests/test_processors/test_validator.py` (ENHANCE EXISTING)

**New Test Cases** (7 tests):
- ✅ AI provider failure during spam detection (fallback to non-spam)
- ✅ Cache corruption handling (invalid cached validation result)
- ✅ Very long content truncation (1000 char limit)
- ✅ Special characters in title/content
- ✅ Unicode handling in spam detection
- ✅ Empty title with valid content
- ✅ All whitespace content with non-empty title

**Success Criteria**:
- Coverage increased from 39% to 90%+ for validator.py
- All error paths covered

---

#### 5.2 Activity Error Handling

**File**: Add to each activity test file

**New Test Cases** (per activity, 3 tests each = 15 total):
- ✅ Redis connection failure (retry behavior)
- ✅ Database connection failure (for relevance activity)
- ✅ Invalid input schema (Pydantic validation errors)

**Success Criteria**:
- All error paths in activities covered
- Graceful failure behavior verified

---

#### 5.3 Cache Key Consistency Tests

**File**: `tests/test_temporal/test_cache_keys.py` (NEW)

**Test Cases** (8 tests):
- ✅ Validation cache key determinism
- ✅ Quality cache key determinism
- ✅ Topics cache key determinism
- ✅ Relevance cache key determinism (with profile variations)
- ✅ Cache key collision detection
- ✅ Cache key format validation (prefix:{hash} pattern)
- ✅ Cache TTL configuration per activity
- ✅ Cache key uniqueness across activities

**Success Criteria**:
- Validates cache key strategy across all activities
- Ensures no key collisions

---

## Test Organization

### Directory Structure

```
tests/
├── test_processors/
│   ├── test_validator.py                      # ENHANCE: +7 tests
│   └── test_normalizer.py                     # UPDATE: remove validation tests
├── test_temporal/
│   ├── test_activities_validation.py          # NEW: 12 tests (validate_and_filter_batch)
│   ├── test_activities_quality.py             # NEW: 10 tests (score_quality_batch)
│   ├── test_activities_topics.py              # NEW: 11 tests (extract_topics_batch)
│   ├── test_activities_processing.py          # UPDATE: clean up normalize tests
│   ├── test_activities_integration.py         # NEW: 5 integration tests
│   ├── test_workflow_integration.py           # ENHANCE: +4 tests
│   ├── test_worker.py                         # NEW: 6 tests
│   ├── test_client.py                         # ENHANCE: +8 tests
│   └── test_cache_keys.py                     # NEW: 8 tests
└── conftest.py                                # UPDATE: add fixtures for new tests
```

### Test Markers

```python
# Unit tests (no Docker required)
@pytest.mark.unit

# Integration tests (require Docker)
@pytest.mark.integration

# Slow tests (> 1 second)
@pytest.mark.slow
```

### Running Tests

```bash
# All tests (requires Docker)
uv run pytest

# Unit tests only (no Docker)
uv run pytest -m unit

# Integration tests only
uv run pytest -m integration

# Coverage report
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

---

## Success Metrics

### Coverage Targets

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `app/processors/validator.py` | 39% | 90% | **P1** |
| `app/temporal/activities/processing.py` | 18% | 85% | **P1** |
| `app/temporal/worker.py` | 0% | 100% | **P1** |
| `app/temporal/workflows.py` | 42% | 80% | **P1** |
| `app/temporal/client.py` | 21% | 85% | **P2** |
| **Overall Backend** | **42%** | **85%** | **GOAL** |

### Test Count Targets

| Category | Current | Target | Net Change |
|----------|---------|--------|------------|
| Unit tests | ~50 | ~120 | **+70** |
| Integration tests | ~15 | ~25 | **+10** |
| **Total** | **~65** | **~145** | **+80** |

### Quality Metrics

- ✅ All tests passing (no skipped tests without good reason)
- ✅ Test execution time < 30 seconds for unit tests
- ✅ Test execution time < 5 minutes for full suite (with Docker)
- ✅ No flaky tests (tests pass consistently)
- ✅ Clear test documentation (docstrings for complex tests)

---

## Implementation Schedule

### Week 1: Foundation (Unit Tests)

**Days 1-2**: Phase 1.1 - Validation activity tests (12 tests)
**Days 3-4**: Phase 1.2 - Quality activity tests (10 tests)
**Day 5**: Phase 1.3 - Topics activity tests (11 tests)

**Deliverable**: 33 new unit tests, +30% coverage for processing.py

---

### Week 2: Integration & Infrastructure

**Days 1-2**: Phase 2 - Update existing tests (refactor normalize/validation split)
**Days 3-4**: Phase 3.1 - End-to-end integration tests (5 tests)
**Day 5**: Phase 4 - Worker and client tests (14 tests)

**Deliverable**: 19 new tests + refactored tests, workflow.py coverage to 80%

---

### Week 3: Edge Cases & Polish

**Days 1-2**: Phase 3.2 - Workflow integration enhancement (4 tests)
**Days 3-4**: Phase 5 - Edge cases and error paths (30 tests)
**Day 5**: Review, documentation, final coverage validation

**Deliverable**: 34 new tests, 85%+ overall coverage achieved

---

## Risk Mitigation

### Risk 1: Docker Infrastructure Required

**Mitigation**:
- Prioritize unit tests (no Docker) in Phase 1
- Use pytest markers to separate unit/integration tests
- Document Docker setup clearly in CONTRIBUTING.md
- Consider using pytest-docker-compose for easier setup

### Risk 2: Flaky Tests (External Dependencies)

**Mitigation**:
- Use proper mocking for unit tests
- Add retries for integration tests (Temporal operations)
- Use fixed test data (avoid time-dependent assertions)
- Use pytest-timeout to catch hanging tests

### Risk 3: Test Maintenance Burden

**Mitigation**:
- Use shared fixtures (DRY principle)
- Group related tests in classes
- Document test purpose clearly
- Refactor tests as code evolves

---

## Appendix: Test Fixtures

### Key Fixtures Needed

```python
# conftest.py additions

@pytest.fixture
def sample_raw_articles() -> list[Article]:
    """Raw articles before validation."""
    # ...

@pytest.fixture
def sample_validated_articles() -> list[Article]:
    """Articles that passed validation."""
    # ...

@pytest.fixture
def sample_normalized_articles() -> list[Article]:
    """Articles after normalization."""
    # ...

@pytest.fixture
def mock_validator() -> Mock:
    """Mocked ContentValidator."""
    # ...

@pytest.fixture
def mock_quality_scorer() -> Mock:
    """Mocked QualityScorer."""
    # ...

@pytest.fixture
def mock_topic_extractor() -> Mock:
    """Mocked TopicExtractor."""
    # ...

@pytest.fixture
def mock_redis_client() -> Mock:
    """Mocked Redis client."""
    # ...

@pytest.fixture
def mock_temporal_client() -> Mock:
    """Mocked Temporal client."""
    # ...
```

---

## Next Steps

1. **Review Plan**: Get stakeholder approval for scope and timeline
2. **Set Up Environment**: Ensure Docker is available for integration tests
3. **Start Phase 1**: Begin with validation activity unit tests (highest priority)
4. **Track Progress**: Update this document as tests are completed
5. **Continuous Monitoring**: Run coverage reports daily to track progress

---

**Document Owner**: Development Team
**Last Updated**: 2025-11-05
**Status**: Draft (Awaiting Approval)
