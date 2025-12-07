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

## 5. Service Layer Pattern

Services encapsulate business logic and coordinate between repositories to perform complex operations. They manage transaction boundaries and raise appropriate HTTP exceptions for business rule violations.

**Architecture:**

```
API Endpoint → Service → Repositories → Database
     ↓              ↓
  HTTP only    Business Logic + Transactions
```

**Service Structure:**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def update_timezone(self, user: User, timezone: str) -> User:
        """Update user timezone. Service commits transaction."""
        user.timezone = timezone
        updated_user = await self.user_repo.update(user)
        await self.session.commit()
        await self.session.refresh(updated_user)
        return updated_user
```

**API Layer Usage:**

```python
from app.services.user_service import UserService

@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """API endpoint handles HTTP only."""
    user_service = UserService(session)
    updated_user = await user_service.update_timezone(
        user=current_user,
        timezone=profile_update.timezone,
    )

    return UserProfile(
        id=updated_user.id,
        email=updated_user.email,
        timezone=updated_user.timezone,
        is_verified=updated_user.is_verified,
        is_active=updated_user.is_active,
    )
```

**Key Principles:**

- **Services commit transactions** - Not API layer or repositories
- **Services raise HTTPException** - Business rule violations use appropriate status codes
- **Services coordinate repositories** - Multi-step operations orchestrated in service layer
- **API layer stays thin** - Only request/response handling, no business logic
- **Repositories are data-only** - No business logic, just CRUD operations
- **One service per domain** - AuthService for auth, UserService for users, ConfigService for config

**Transaction Management:**

Services control transaction boundaries:

```python
async def register_user(self, email: str, password: str, timezone: str) -> User:
    """Multi-step transaction: all or nothing."""
    # Create user
    new_user = User(email=email, hashed_password=get_password_hash(password), ...)
    created_user = await self.user_repo.create(new_user)

    # Create config
    default_config = DigestConfiguration(user_id=created_user.id, ...)
    self.session.add(default_config)
    await self.session.flush()

    # Create profile
    default_profile = InterestProfile(config_id=default_config.id, ...)
    self.session.add(default_profile)

    # Atomic commit
    await self.session.commit()
    await self.session.refresh(created_user)

    return created_user
```

**Error Handling in Services:**

```python
async def get_user_config(self, user_id: str) -> tuple[DigestConfiguration, list[ContentSource], InterestProfile]:
    """Fetch complete config. Raises 404 if not found."""
    _, config = await self.config_repo.get_user_with_config(user_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digest configuration not found",
        )

    sources = await self.source_repo.get_active_for_config(config.id)
    profile = await self.config_repo.get_interest_profile(config.id)

    return config, sources, profile
```

**Anti-Patterns to Avoid:**

- ❌ No `BaseService` class - wait for actual shared code (YAGNI)
- ❌ No repository injection into services - create inline from session
- ❌ No stateful services - each instance lives for one request
- ❌ No mixed transaction boundaries - service commits XOR API commits
- ❌ No business logic in API layer - move it to services
- ❌ No business logic in repositories - keep them data-only

## 6. Error Handling Strategy

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
