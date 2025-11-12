# Key Dependencies

## Runtime Dependencies

### Web Framework

- **FastAPI** (>=0.116.2): Modern async Python web framework
  - Used for: API routes, automatic OpenAPI docs, request validation
  - Why: High performance, Pydantic integration, excellent async support

### Database

- **SQLAlchemy** (>=2.0.43): SQL toolkit and ORM
- **SQLModel** (>=0.0.25): Combines SQLAlchemy with Pydantic models
  - Used for: Database models, validation, serialization
  - Why: Type-safe, validation at both DB and API level
- **asyncpg** (>=0.30.0): PostgreSQL async driver
- **psycopg[binary]** (>=3.2.10): PostgreSQL adapter with C bindings
- **Alembic** (>=1.16.5): Database migrations
  - Used for: Schema versioning, rollback capability
  - Why: Version control for database changes

### Content Processing

- **feedparser** (>=6.0.12): RSS/Atom feed parsing
- **BeautifulSoup4** (>=4.13.5): HTML parsing and cleaning
- **lxml** (>=6.0.1): XML/HTML processing (fast C implementation)
- **aiohttp** (>=3.12.15): Async HTTP client
  - Used for: Fetching feeds, HTTP requests with retry logic
  - Why: Async, connection pooling, timeout handling

### AI Integration

- **PydanticAI** (>=1.0.8): AI framework with structured output
  - Used for: Summarization, topic extraction, similarity analysis
  - Why: Type-safe AI calls, structured responses, easy provider switching

### Caching

- **redis** (>=6.4.0): Redis client
  - Used for: Caching similarity results, session management
  - Why: High-performance distributed cache
- **fakeredis** (dev): In-memory Redis mock for testing

### Authentication & Security

- **python-jose[cryptography]** (>=3.5.0): JWT tokens
- **passlib[bcrypt]** (>=1.7.4): Password hashing
  - Used for: User authentication, secure password storage
  - Why: Industry-standard algorithms

### Utilities

- **pydantic-settings** (>=2.10.1): Settings management from environment
- **python-dotenv** (>=1.1.1): Load .env files
- **email-validator** (>=2.3.0): Email validation
- **python-ulid** (>=3.1.0): ULID generation for IDs
- **loguru** (>=0.7.3): Structured logging
  - Used for: Application logging
  - Why: Clean API, automatic formatting, file rotation

### HTTP Server

- **uvicorn** (>=0.35.0): ASGI web server
- **python-multipart** (>=0.0.20): Multipart form data parsing

### Workflow Orchestration

- **temporalio** (>=1.17.0): Temporal Python SDK
  - Used for: Distributed workflow execution, activity orchestration
  - Why: Fault tolerance, durable execution, event sourcing

## Development Dependencies

### Testing

- **pytest** (>=8.4.2): Test framework
- **pytest-asyncio** (>=1.2.0): Async test support
- **pytest-cov** (>=7.0.0): Coverage reporting
- **pytest-xdist** (>=3.8.0): Parallel test execution (`-n auto`)
- **pytest-timeout** (>=2.4.0): Test timeout handling
- **pytest-mock-resources** (>=2.12.4): Test database/service mocking
- **httpx** (>=0.28.1): Async HTTP client for testing

### Code Quality

- **ruff** (>=0.13.0): Fast Python linter and formatter
  - Replaces: black, flake8, isort, pylint (partially), pyupgrade
  - Why: Single tool, blazing fast, excellent Python 3.13 support
- **mypy** (>=1.18.1): Static type checker
  - Used for: Type safety validation
  - Why: Catches type errors before runtime

### Docker Testing

- **python-on-whales** (>=0.78.0): Docker SDK for Python

## Why These Choices

### Async-First Architecture

- aiohttp, asyncpg, uvicorn, FastAPI: Built for async/await from the start
- Allows handling thousands of concurrent requests with minimal resources

### Type Safety

- SQLModel + Pydantic: Type hints everywhere, validation at boundaries
- MyPy: Catch errors at development time, not production
- FastAPI: Automatic OpenAPI docs from types

### Performance

- asyncpg: Async PostgreSQL driver (much faster than sync psycopg2)
- Ruff: 10x faster than black/flake8 combined
- Redis: Sub-millisecond caching layer

### Simplicity

- Temporal: Complex workflows without building state machines
- PydanticAI: AI calls with structured outputs, easy provider switching
- SQLModel: No separate serialization layer (Pydantic models are DB models)

### Development Experience

- FastAPI: Auto-generated API docs, request validation, awesome errors
- Loguru: Beautiful structured logging without boilerplate
- Makefile: Common commands always available

## Adding New Dependencies

1. Add to `pyproject.toml` in appropriate section
2. Run `uv sync` to update lock file
3. Document in this memory file if significant
4. Update `backend/CLAUDE.md` if adding new subsystem (e.g., new AI provider)
5. Add tests to verify integration
