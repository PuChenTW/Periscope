# Testing Strategy

## 1. Test Structure

Organize tests into layers that mirror the application architecture. This makes tests easy to find and maintain while ensuring comprehensive coverage.

### Test Organization

```
tests/
├── unit/                      # Unit tests for individual components
│   ├── processors/           # Content processing tests
│   │   ├── test_rss_fetcher.py
│   │   ├── test_ai_provider.py
│   │   ├── test_similarity_detector.py
│   │   └── test_topic_extractor.py
│   ├── services/             # Service layer tests
│   ├── repositories/         # Repository tests
│   └── utils/               # Utility function tests
│
├── integration/              # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   └── test_content_pipeline.py
│
├── temporal/                 # Temporal workflow tests
│   ├── test_digest_workflow.py
│   ├── test_onboarding_workflow.py
│   └── test_activities.py
│
├── fixtures/                 # Shared test fixtures
│   ├── database.py          # Database fixtures
│   ├── sample_data.py       # Test data fixtures
│   └── mocks.py             # Mock objects
│
└── conftest.py              # Pytest configuration
```

## 2. Testing Guidelines

### Unit Tests
Test individual functions/methods in isolation with mocked dependencies.

**Characteristics:**
- Fast execution (milliseconds per test)
- No external dependencies (databases, APIs, file systems)
- Test one thing at a time
- Use mocks and stubs liberally
- Cover edge cases and error conditions

**Example Focus Areas:**
- Business logic validation
- Data transformation
- Error handling
- Input validation
- Algorithm correctness

### Integration Tests
Test component interactions including API endpoints and database operations.

**Characteristics:**
- Test multiple components working together
- Use test database and real connections
- Test API endpoints end-to-end
- Verify database state changes
- Check external service integrations (with mocks)

**Example Focus Areas:**
- API endpoint request/response flows
- Database transactions and rollback
- Service-to-repository interactions
- Authentication and authorization flows
- Error propagation between layers

### Workflow Tests
Use Temporal's test framework for workflow and activity testing.

**Characteristics:**
- Test workflows in isolation using Temporal test environment
- Mock activities to test workflow logic
- Test activities independently with real implementations
- Verify workflow state transitions
- Test timeout and retry behavior

**Example Focus Areas:**
- Workflow orchestration logic
- Activity execution order
- Error handling and compensation
- Retry policies
- Workflow state persistence

### Database Tests
Use dedicated test database with proper cleanup between tests.

**Characteristics:**
- Isolated test database per test worker
- Transaction rollback after each test
- Use fixtures for common data setups
- Test database constraints and relationships
- Verify indexes and query performance

**Setup Requirements:**
- Separate test database (never use production)
- Automatic schema migration
- Data cleanup after tests
- Connection pool management

### Mock External Services
Avoid hitting real APIs in tests, use mocks for external dependencies.

**Mocking Strategy:**
- Mock HTTP clients for external APIs
- Mock AI providers for content processing
- Mock email services
- Use fixtures for consistent mock data
- Provide realistic mock responses

**Tools:**
- `pytest-mock` for general mocking
- `responses` for HTTP mocking
- Custom mock fixtures for AI providers

### RSS Feed Processing Tests
Comprehensive test suite covering HTTP client, URL validation, RSS/Atom parsing, factory pattern, and error handling scenarios.

**Coverage Areas:**
- HTTP client with native aiohttp exceptions
- URL validation (format, scheme, accessibility)
- RSS 2.0 and Atom 1.0 parsing
- Factory pattern fetcher selection
- Error handling with retry logic
- Content extraction and cleaning
- Metadata extraction
- Timeout and network error scenarios
- Malformed feed handling

### AI Provider Tests
Mock AI provider interface for deterministic testing without calling real AI APIs.

**Mocking Strategy:**
- Protocol-based mock implementation
- Deterministic responses for test cases
- Error simulation for failure scenarios
- No actual AI API calls in tests

**Coverage:**
- Provider factory creation
- Agent creation with different models
- Structured output parsing
- Error handling and fallbacks

### Similarity Detection Tests
Test suite with mock AI provider for grouping logic, topic aggregation, and caching behavior.

**Coverage Areas:**
- Article pairwise comparison
- Similarity scoring and threshold filtering
- Connected components grouping algorithm
- Topic aggregation from grouped articles
- Redis caching behavior
- Error handling with fallback
- Empty input handling
- Edge cases

### Topic Extraction Tests
Test suite covering topic extraction, error handling, content validation, and max topics enforcement.

**Coverage Areas:**
- Topic extraction from article content
- Content truncation handling
- Max topics limit enforcement
- Structured output validation
- Error handling with fallback
- Empty/invalid content handling
- AI provider integration
- Cache behavior

**Testing Approach:**
- Use mock AI provider for deterministic results
- Test with custom TopicExtractionSettings for different max_topics values
- Verify extraction works independently for multiple articles
- Test error handling returns empty list gracefully

### Summarization Tests
Test suite covering multiple summary styles, custom prompts with validation, and error handling.

**Coverage Areas:**
- Multiple summary styles (brief, detailed, bullet_points)
- Custom prompt validation (pattern-based and AI-powered)
- Summary length enforcement
- Content truncation for AI processing
- Topic integration in prompts
- Error handling with content excerpts as fallback
- Minimal content handling
- Async preparation and validation

**Testing Approach:**
- Use mock AI provider for deterministic summary generation
- Test with custom SummarizationSettings, CustomPromptSettings, AIPromptValidationSettings
- Verify each summary style produces expected format
- Test custom prompt validation rejection and acceptance
- Verify fallback behavior when AI fails

**Key Scenarios:**
- Style variations (brief vs detailed vs bullet points)
- Prompt validation (valid prompts pass, invalid prompts rejected)
- Fallback behavior (excerpts when AI unavailable)
- Content length handling (minimal content uses excerpt)

### Content Normalization Tests
Test suite covering spam detection, length validation, metadata normalization, and date handling.

**Coverage Areas:**
- Content quality validation (length, whitespace)
- AI-powered spam detection
- Title, author, tags normalization
- Date normalization to UTC
- URL tracking parameter removal
- Field truncation enforcement
- Error handling without exceptions

**Testing Approach:**
- Use mock AI provider for spam detection
- Test with custom ContentNormalizationSettings for different thresholds
- Verify normalization never raises exceptions (always returns or None)
- Test all metadata standardization rules

**Key Scenarios:**
- Valid content passes all checks
- Short content rejected
- Spam content detected and rejected
- Metadata cleaned and normalized
- Date handling (naive → UTC, timezone conversion)

### Quality Scoring Tests
Test suite covering metadata scoring, AI quality assessment, and score calculation.

**Coverage Areas:**
- Metadata score calculation (0-50 points)
- AI content quality assessment (0-50 points)
- Combined score calculation (0-100 scale)
- Quality scoring enabled/disabled states
- Error handling with neutral fallback scores
- Score breakdown tracking

**Testing Approach:**
- Use mock AI provider for content quality evaluation
- Test with ContentNormalizationSettings.quality_scoring_enabled toggled
- Verify metadata scoring rules (author, date, tags, length)
- Verify AI scoring fallback on errors

**Key Scenarios:**
- Quality scoring enabled (metadata + AI scores)
- Quality scoring disabled (metadata only, scaled to 100)
- AI errors return neutral scores
- Score breakdown properly tracked in metadata

## 3. Test Configuration Approach

### pytest-mock-resources
Use pytest-mock-resources for PostgreSQL test fixtures with pgvector support.

**Benefits:**
- Automatic database setup and teardown
- Parallel test execution support
- Real PostgreSQL instance for testing
- Extension support (pgvector)

### Separate Test Databases
Configure separate test databases per worker for parallel test execution.

**Configuration:**
- One database per pytest worker
- Automatic cleanup between tests
- Isolated transactions
- Connection pooling per worker

### Session Management
Implement proper session management with automatic cleanup and rollback on test failures.

**Benefits:**
- Test isolation
- No data leakage between tests
- Automatic cleanup
- Consistent test state

## Testing Best Practices

1. **Fast Feedback**: Keep tests fast, especially unit tests
2. **Test Isolation**: Each test should be independent
3. **Clear Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Follow AAA pattern for clarity
5. **One Assertion Focus**: Test one thing per test (when reasonable)
6. **Avoid Test Interdependence**: Tests should not rely on each other
7. **Mock External Services**: Never hit real external APIs
8. **Use Fixtures**: Share common setup via pytest fixtures
9. **Clean Up**: Always clean up resources after tests
10. **Test Error Cases**: Don't just test happy paths

## Coverage Targets

- **Overall Code Coverage**: High coverage across all components
- **Critical Paths**: Full coverage (authentication, data integrity)
- **Business Logic**: Comprehensive coverage
- **Utilities**: Good coverage
- **Integration Points**: Strong coverage

## Continuous Integration

- Run tests on every pull request
- Fail builds on test failures
- Report coverage metrics
- Run linting and type checking
- Parallel test execution for speed
