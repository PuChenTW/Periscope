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

## 3. Session Management with Middleware

Custom ORM session middleware manages database sessions per request. Sessions are automatically created, managed, and cleaned up with proper error handling and rollback support. Dirty session detection prevents uncommitted changes.

**Key Features:**
- Per-request session lifecycle
- Automatic commit on successful responses
- Automatic rollback on exceptions
- Dirty session detection
- Connection pool management

## 4. Error Handling Strategy

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
