# Core Design Principles

## 1. Repository Pattern

Clean separation between business logic and data access layers. Repositories handle all database operations while services contain business logic. This pattern allows for easier testing and maintains single responsibility principle.

**Key Benefits:**

- Business logic isolated from data access details
- Easier to test services with mocked repositories
- Single place to manage database queries
- Consistent data access patterns across the application

## 2. Dependency Injection

Use FastAPI's dependency injection system to manage service dependencies. Database sessions are injected through middleware, and services are composed using dependency providers. This promotes loose coupling and testability.

**Key Benefits:**

- Loose coupling between components
- Easy to swap implementations (testing, different providers)
- Clear dependency graphs
- Automatic resource management and cleanup

## 3. Session Management

Database sessions are injected via FastAPI's dependency injection using `get_async_session()`. Sessions are automatically created, managed, and cleaned up with proper error handling and rollback support.

**Key Features:**

- Per-request session lifecycle via DI
- Callers control transaction boundaries (explicit commits)
- Automatic rollback on exceptions
- Connection pool management

**Transaction Control:**

Callers must explicitly commit when needed:

```python
async def create_user(session: AsyncSession, user_data: UserCreate):
    user = User(**user_data.dict())
    session.add(user)
    await session.commit()  # Explicit commit
    return user
```

Read-only operations don't need commits - the session auto-closes after the request.

## 4. Type Annotations & SQLModel Constraints

**Modern Syntax:**

Use Python 3.10+ native union syntax (`X | None`) for type hints:

```python
def get_user(user_id: str) -> User | None:
    return session.get(User, user_id)
```

**SQLModel Forward Reference Limitation:**

For SQLModel `Relationship` fields with forward references, you **must** use `Optional["ClassName"]` instead of `"ClassName" | None`:

```python
# ✅ Correct - works with SQLModel
digest_config: Optional["DigestConfiguration"] = Relationship(back_populates="user")

# ❌ Broken - TypeError at class definition time
digest_config: "DigestConfiguration" | None = Relationship(back_populates="user")
```

**Why:** Python evaluates `"string" | None` at class definition time, which fails because you can't apply the `|` operator to a string literal. `Optional["Class"]` delays evaluation until runtime.

**When the class is already defined** (no forward reference), use modern syntax:

```python
user: User | None = Relationship(back_populates="digest_config")  # ✅ User is defined above
```

## 5. Error Handling Strategy

Implement hierarchical custom exceptions for different error types (business logic, validation, external services). Use global exception handlers to provide consistent API responses and proper HTTP status codes.

**HTTP Client Exception Handling:**
For HTTP client operations, leverage native aiohttp exceptions (`ClientResponseError`, `TimeoutError`, `ClientError`) rather than custom wrapper exceptions to maintain simplicity and standard library compatibility.

**Key Principles:**

- Use standard library exceptions when appropriate
- Create custom exceptions only for domain-specific errors
- Centralized exception handling at API layer
- Consistent error response format
- Proper HTTP status code mapping
- Logging at appropriate exception levels
