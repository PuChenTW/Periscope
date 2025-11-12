# Development Workflow

## Git Workflow

### Current Status

- **Main Branch**: `main` (stable, production-ready)
- **Platform**: Darwin (macOS)

### Recent Activity (last 5 commits)

1. `c7b1268` - fix: Update test coverage badge to reflect current coverage percentage
2. `1feee49` - docs: Mark Phase 4 complete and document batch processing activities implementation
3. `5dc22d9` - feat: Implement ProcessingActivities class with 5 batch processing activities and workflow integration
4. `f983476` - refactor: Extract validation logic from normalizer into dedicated ContentValidator class
5. `ae4c1f9` - fix: Update test coverage badge to reflect current coverage percentage

### Working with Git

```bash
# Check current status
git status

# View changes
git diff                    # Unstaged changes
git diff --cached          # Staged changes
git log --oneline -n 10    # Recent commits

# Before starting work
git pull origin main       # Get latest from main

# Creating commits
git add <files>
git commit -m "type: Brief description"

# Common commit types: feat:, fix:, refactor:, docs:, test:, style:, chore:
```

## Development Workflow Steps

### Starting a New Task

1. **Ensure you're on main and up to date**

   ```bash
   git checkout main
   git pull origin main
   ```

2. **Understand the requirements**
   - Read the task description carefully
   - Check related CLAUDE.md files
   - Review existing code patterns

3. **Plan your approach**
   - Identify which files need changes
   - Check for existing patterns to follow
   - Consider test coverage needed
   - Ask questions if anything is unclear

### During Development

1. **Follow the code style**
   - Use the style guide in `code_style_and_conventions.md`
   - IDE should handle formatting with Ruff integration

2. **Keep commits small and focused**
   - One logical change per commit
   - Commit messages should be clear (type: description)

3. **Write tests as you go**
   - Test coverage target: 80%+
   - Write tests that demonstrate the feature works
   - Use pytest async support for async code

4. **Run quality checks frequently**

   ```bash
   make lint        # Check for style issues
   make format      # Auto-format code
   make test        # Run all tests
   ```

### Before Committing

1. **Ensure all tests pass**

   ```bash
   make test
   ```

2. **Check code quality**

   ```bash
   make lint
   ```

3. **Format code**

   ```bash
   make format
   ```

4. **Use the task completion checklist**
   - Reference `task_completion_checklist.md`
   - Verify all items before committing

### Submitting Work

1. **Verify one final time**

   ```bash
   make test
   make lint
   ```

2. **Create meaningful commit message**
   - Use conventional commit format: `type: description`
   - Explain WHAT changed and WHY
   - Reference issue numbers if applicable

3. **Push to remote (if applicable)**

   ```bash
   git push origin branch-name
   ```

## Common Development Scenarios

### Writing Tests for New Feature

1. Check `docs/testing-strategy.md` for approach
2. Create test file in `tests/` matching module structure
3. Use fixtures from `tests/conftest.py`
4. Write async tests with `@pytest.mark.asyncio`
5. Mock external dependencies (AI providers, HTTP calls)
6. Run with `uv run pytest tests/test_feature.py -v`

### Adding Database Changes

1. Modify model in `app/models/`
2. Create migration: `make mg-rev MESSAGE="description"`
3. Review generated migration in `alembic/versions/`
4. Test migration: `make mg` to upgrade, `make mg-down` to downgrade
5. Update related services/repositories
6. Write tests for new fields/relationships

### Working with Temporal Workflows

1. Check `docs/temporal-workflows.md`
2. Implement activity in `app/temporal/activities/`
3. Update workflow in `app/temporal/workflows.py`
4. Add activity to worker in `app/temporal/worker.py`
5. Write integration tests in `tests/test_temporal/`
6. Test with local Temporal server (via Docker)

### Adding New API Endpoint

1. Create route in `app/api/`
2. Create request/response models (FastAPI will use Pydantic validation)
3. Delegate logic to service layer
4. Add tests to `tests/integration/`
5. Update `docs/architecture.md` if architecture changes
6. Test with `make dev` and visit `/docs`

## Environment Setup

### .env Configuration

- Copy `.env.example` to `.env`
- Configure required settings for your development
- Never commit actual secrets
- Use test values for development

### Database Setup

```bash
make dev              # Starts PostgreSQL automatically
# Or manually:
docker compose up -d postgres
make mg              # Run migrations
```

### Testing Database

- Tests use temporary PostgreSQL containers via pytest-mock-resources
- Cleaned up automatically after test run
- Clean stale containers: `make test-clean`

## Debugging

### View Logs

```bash
make logs             # Docker Compose logs
```

### Database Debugging

```bash
make db-shell        # Direct PostgreSQL access
```

### API Debugging

```bash
curl -X GET http://localhost:8000/docs    # Swagger UI
curl -X GET http://localhost:8000/health   # Health check
```

### Test Debugging

```bash
# Run single test with output
uv run pytest tests/test_file.py::test_name -v -s

# Run with pdb on failure
uv run pytest tests/ --pdb
```

## Performance & Optimization

### Profiling

- Use Python's `cProfile` for CPU profiling
- Use `memory_profiler` for memory analysis
- Track performance in commit messages when optimizing

### Caching

- Use Redis cache for expensive operations
- Default TTL strategies documented in `app/processors/`
- Test cache behavior in integration tests

### Database Queries

- Ensure proper indexing on frequently queried fields
- Use SQLAlchemy's `select()` API for clarity
- Use `joinedload()` to prevent N+1 queries
- Profile queries before declaring them optimized

## Common Commands Reference

```bash
make help           # Show all available make commands
make install        # First-time setup
make dev            # Start development (includes DB)
make test           # Run all tests
make lint           # Check code quality
make format         # Auto-format code
make mg             # Run pending migrations
make db-shell       # Open PostgreSQL shell
make clean          # Clean temporary files
```
