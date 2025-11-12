# Task Completion Checklist

When completing work on features, bug fixes, or refactoring, follow these steps:

## Code Quality Checks

- [ ] **Run linting**: `make lint` - Fix any ruff or mypy errors
- [ ] **Format code**: `make format` - Ensure consistent formatting
- [ ] **Run all tests**: `make test` - Ensure no regressions
- [ ] **Check coverage**: `make test-cov` - Verify adequate test coverage (target: 80%+)

## Code Review Checklist

- [ ] **No commented-out code**: Remove any commented code (use git for history)
- [ ] **Docstrings complete**: Google-style docstrings on public functions/classes
- [ ] **Type hints present**: All function signatures include type hints and return types
- [ ] **Names are clear**: Variables, functions, classes have descriptive names
- [ ] **No print statements**: Only logging via loguru in production code
- [ ] **Error handling complete**: Domain errors raised, API layer handles HTTP translation
- [ ] **Functions are focused**: Each function does one thing well
- [ ] **No boolean arguments**: Split functions instead of using boolean flags

## Database Changes

- [ ] **Migrations created**: If schema changed, run `make mg-rev MESSAGE="description"`
- [ ] **Migrations tested**: Verify `make mg` runs successfully
- [ ] **Models updated**: SQLModel definitions match database schema
- [ ] **Docstrings on models**: Database models have field descriptions

## Temporal Workflow Changes (if applicable)

- [ ] **Activities documented**: Activity purpose, inputs, outputs documented
- [ ] **Workflow tested**: Integration tests verify workflow execution
- [ ] **Retry logic appropriate**: Different retry strategies for different activities
- [ ] **Error handling**: Activities raise meaningful exceptions

## Tests Updated

- [ ] **New features have tests**: Aim for >80% coverage
- [ ] **Tests are focused**: Test one behavior per test
- [ ] **No redundant tests**: Delete tests that duplicate behavior checks
- [ ] **Mock providers used**: AI provider calls mocked in tests
- [ ] **Async tests correct**: Use `@pytest.mark.asyncio` for async tests

## Documentation

- [ ] **CLAUDE.md updated**: Reflect architectural changes if significant
- [ ] **API docs current**: FastAPI auto-docs are accurate
- [ ] **Inline comments explain WHY**: Comments justify design decisions
- [ ] **README reflects reality**: Update if new features or setup changes

## Final Steps

- [ ] **All tests pass**: `make test` runs cleanly
- [ ] **Linting passes**: `make lint` shows no errors
- [ ] **No merge conflicts**: Branch is up to date with main
- [ ] **Commit messages clear**: Explain WHAT changed and WHY

## Phase Completion Checklist

When completing a full phase/feature:

- [ ] All individual tasks above completed
- [ ] Integration tests verify end-to-end functionality
- [ ] Performance profiled (no obvious bottlenecks)
- [ ] Security review for sensitive operations
- [ ] Temporal workflows validated at scale (if applicable)
- [ ] Redis caching working as expected (if used)
- [ ] Email delivery tested (if applicable)
