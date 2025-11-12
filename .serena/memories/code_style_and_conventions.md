# Code Style and Conventions

## Ruff Configuration

- **Target Python Version**: 3.13
- **Line Length**: 120 characters
- **Indent Width**: 4 spaces
- **Quote Style**: Double quotes (`"string"`)
- **Docstring Convention**: Google-style

## Import Formatting

- Configured with isort
- Single-line imports forced when possible
- First-party known module: `app`
- Combine imports like `from module import foo, bar as b` allowed

## Code Quality Rules

### Enabled Lint Rules

- E, W: pycodestyle errors/warnings
- F: Pyflakes
- I: isort
- N: pep8-naming (naming conventions)
- D: pydocstyle (Google docstrings)
- UP: pyupgrade
- B: flake8-bugbear
- A: flake8-builtins (no shadowing builtins)
- C4: flake8-comprehensions
- T20: flake8-print (catch print statements)
- SIM: flake8-simplify (simplify code)
- ARG: flake8-unused-arguments
- PTH: flake8-use-pathlib
- ERA: eradicate (detect commented code)
- PL: Pylint
- RUF: Ruff-specific rules

### Disabled Rules (Important)

- D100-D107: Docstring requirements per function (disabled for dev flexibility)
- D203, D212-213, D400-401, D415: Docstring format variations
- PLR0913: Allow up to 10 function arguments
- PLR2004: Allow magic values in comparisons
- T20: Allow print statements in development
- ERA001: Allow commented code (for development)

### Test File Special Handling

- No docstring requirements in `tests/`
- Allow unused arguments (ARG)
- Allow magic values (PLR2004)

## Naming Conventions

- Use descriptive names that reveal intent
- Short names for short scopes (i, j for loops)
- Longer names for wider scopes and public APIs
- No Hungarian notation or type prefixes
- Follow PEP 8 naming: `snake_case` for functions/variables, `PascalCase` for classes

## Function Design

- Functions should do ONE thing well
- Keep functions short (fit on screen ideally)
- Minimize arguments (≤3 preferred, max 5)
- Return early, avoid deep nesting
- Avoid boolean arguments (split functions instead)
- Docstrings explain WHY not WHAT

## Error Handling

- Raise domain-specific exceptions in services/repositories
- Let API layer translate to HTTP responses
- Never silently swallow exceptions
- Clean up resources in reverse order of acquisition
- Fail fast and loudly during development

## Comments & Documentation

- Code should be self-documenting
- Comment WHY, not WHAT
- Document invariants, assumptions, non-obvious side effects
- Include TODO comments with owner and date
- Remove commented-out code (use version control instead)
- Document lock ordering, concurrency assumptions, performance considerations

## Architecture Principles

- **Data structures first**: Get data structures right, code follows naturally
- **Modularity**: One module, one responsibility
- **Functional-first**: Prefer pure functions + composition over classes (except where framework requires it)
- **DI Pattern**: Use dependency injection for testability, especially in services/repositories

## Anti-Patterns to Avoid

- Speculative generality (don't solve problems you don't have)
- Premature abstraction (wait for patterns to emerge)
- Enterprise patterns (AbstractSingletonProxyFactoryBean nonsense)
- Resume-driven development (use boring technology that works)
- Over-abstraction (2-3 layers maximum)

## Type Hints

- Use type hints for all function signatures
- Include return types
- Use `Optional[]` for nullable types, not `Union[T, None]`
- Use Pydantic models for request/response schemas

## SQLModel & Database

- Use SQLModel for ORM (combines SQLAlchemy + Pydantic)
- Async queries with asyncpg
- Keep models simple and focused
- Use Alembic for migrations
- Add migrations with `make mg-rev MESSAGE="description"`

## Testing Strategy

- Write code that's easy to test
- Mock AI providers for deterministic testing
- Keep tests concise (cover each behavior once)
- Integration tests catch more bugs than unit tests
- Use fixtures rather than inline mocks
- Use pytest with asyncio support for async code
- Use `pytest-xdist` for parallel test execution

## Repository & Service Pattern

- **Repositories**: Data access layer, database operations only
- **Services**: Business logic layer, orchestration
- **API**: Request validation and response formatting
- Dependency injection to decouple layers
