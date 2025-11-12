# Essential Commands for Periscope Development

## Installation & Setup

```bash
cd backend/
make install          # Install dependencies with UV
make dev              # Start development environment (PostgreSQL + FastAPI with reload)
make start            # Start all services (Docker Compose)
make stop             # Stop all services
```

## Running Code

```bash
uv run python main.py                    # Run directly with UV (use for any Python script)
uv run uvicorn app.main:create_app ...   # Run FastAPI server
uv run alembic upgrade head              # Run database migrations to latest
uv run alembic downgrade -1              # Downgrade 1 migration step
```

## Testing

```bash
make test             # Run all tests with pytest (parallel with xdist)
make test-cov         # Run tests with coverage report
uv run pytest tests/unit/test_foo.py     # Run specific test file
uv run pytest -k test_name               # Run tests matching pattern
uv run pytest --cov=./app tests/         # With coverage output
```

## Code Quality

```bash
make lint             # Run linting (ruff check + mypy)
make format           # Auto-format code with ruff
uv run ruff check app/ tests/            # Lint only
uv run ruff format app/ tests/           # Format only
uv run mypy app/                         # Type checking only
```

## Database Management

```bash
make mg                              # Migrate to latest (REVISION=head by default)
make mg-heads                        # List all migration heads
make mg-down                         # Downgrade 1 step (STEP=1 by default)
make mg-rev MESSAGE="description"    # Create new auto-generated migration
make mg-merge                        # Merge multiple heads (use with caution)
make db-shell                        # Open PostgreSQL shell
```

## Cleanup

```bash
make clean            # Remove __pycache__, .pyc, coverage files
make test-clean       # Remove test Docker containers
```

## Health & Debugging

```bash
make health           # Check API health endpoint
make logs             # Show Docker Compose service logs
curl http://localhost:8000/docs      # Access Swagger UI
```

## Important: Always use UV

- **Do not** run `python` directly, use `uv run python`
- **Do not** run `pytest` directly, use `uv run pytest`
- **Do not** run `alembic` directly, use `uv run alembic`
- UV manages all Python dependencies and virtual environments

## Git Operations

```bash
git status            # Check current branch and changes
git diff              # View unstaged changes
git log --oneline -n 5 # View recent commits
```
