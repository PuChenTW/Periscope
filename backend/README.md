# Personal Daily Reading Digest - Backend

This is the Phase 1 MVP backend for the Personal Daily Reading Digest platform, built with FastAPI.

## Current Status

**Completed Phase 1+ Features:**
- Core FastAPI application structure
- Database models with SQLAlchemy (PostgreSQL ready)
- Memory-based caching layer (Redis-compatible interface)
- Mock API endpoints for authentication, user management, and digest operations
- **RSS Feed Fetching Layer** (✅ **NEW - COMPLETED**)
  - RSS/Atom feed parsing and validation
  - Simplified async HTTP client with streamlined retry logic and native aiohttp exception handling
  - Content extraction and metadata processing
  - Comprehensive test suite (73 tests passing)
- Docker development environment
- Basic testing setup
- Alembic migrations (ready for database setup)

## Architecture

```
app/
   api/            # API endpoints and routes
   models/         # SQLAlchemy database models
   processors/     # Content processing engines (✅ NEW)
      fetchers/    # RSS/Atom feed fetchers and factory
      utils/       # HTTP client and validation utilities
   utils/          # Utilities (cache, logging, etc.)
   services/       # Business logic (planned for Phase 2)
   repositories/   # Data access layer (planned for Phase 2)
   config.py       # Configuration management
   database.py     # Database connection setup
   main.py         # FastAPI application factory
```

## Quick Start

### Prerequisites
- Python 3.13+
- Docker & Docker Compose
- UV (Python package manager)

### Development Setup

1. **Clone and navigate to backend:**
   ```bash
   cd backend/
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development environment:**
   ```bash
   make dev
   ```
   This starts PostgreSQL in Docker and runs the FastAPI app locally with auto-reload.

5. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Available Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make start         # Start all services with Docker
make dev           # Start development environment
make test          # Run tests
make lint          # Check code quality
make format        # Format code
make clean         # Clean temporary files
```

## API Endpoints

### Health & Monitoring
- `GET /health/` - Basic health check
- `GET /health/ready` - Readiness check (database + cache)

### Authentication (Mock)
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/verify-email` - Email verification
- `POST /auth/forgot-password` - Password reset

### User Management (Mock)
- `GET /users/me` - Get user profile
- `PUT /users/me` - Update user profile
- `GET /users/config` - Get digest configuration
- `PUT /users/config` - Update digest configuration
- `POST /users/sources` - Add content source
- `DELETE /users/sources/{id}` - Remove content source
- `PUT /users/interest-profile` - Update interest keywords

### Digest Operations (Mock)
- `GET /digest/preview` - Preview digest content
- `POST /digest/send-now` - Trigger immediate digest
- `GET /digest/delivery-history` - Get delivery logs
- `GET /digest/sources/validate` - Validate source URL

## Database Schema

Key models implemented:
- **User**: Authentication and profile data
- **DigestConfiguration**: User delivery preferences
- **ContentSource**: RSS feeds and blog URLs
- **InterestProfile**: User interest keywords
- **DeliveryLog**: Delivery history and status

## Cache Layer

The memory-based cache implements a Redis-compatible interface:

```python
from app.utils.cache import get_cache

cache = await get_cache()
await cache.set("key", "value", ttl=300)  # 5 minutes TTL
value = await cache.get("key")
```

**Easy Redis Migration**: Simply swap `MemoryCache` with `RedisCache` in Phase 2.

## Testing

```bash
make test  # Run all tests
```

Current test coverage includes:
- API endpoint functionality
- Mock data validation
- Basic integration tests
- **RSS Feed Fetching Layer** (✅ **NEW**)
  - Simplified HTTP client with unified error handling and native aiohttp exceptions
  - URL validation and RSS feed parsing
  - Integration workflows and edge cases

## Docker Setup

### Development
```bash
docker compose up -d postgres  # PostgreSQL only
# Run app locally with make dev
```

### Full Docker Environment
```bash
docker compose up -d  # All services in containers
```

## Next Phase (Phase 2)

Phase 1+ provides the RSS fetching foundation. Phase 2 will add:
- Business service layer implementation
- AI integration with PydanticAI for summarization
- Temporal workflow implementation
- Redis cache replacement
- Email delivery service

## Environment Variables

Key configuration options:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SECRET_KEY=your-secret-key
DEBUG=true
EMAIL_PROVIDER=smtp
SMTP_HOST=localhost
CACHE_TTL_MINUTES=60
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

All endpoints return JSON and include proper OpenAPI specifications with request/response models.

## RSS Feed Processing

The RSS Feed Fetching Layer provides robust content processing capabilities:

### Features
- Support for RSS 2.0 and Atom 1.0 feeds
- Automatic content type detection and validation
- Simplified error handling using native aiohttp exceptions for better maintainability
- Configurable timeouts and streamlined retry logic with fixed delays
- HTML content cleaning and text normalization
- Unified exception handling for HTTP errors, timeouts, and rate limiting

### Usage
The layer includes factories for automatic fetcher creation and comprehensive content extraction with metadata processing. Supports both individual article fetching and bulk feed processing with graceful error recovery.

### Testing
Comprehensive test suite with 73 passing tests covering:
- Unit tests for simplified HTTP client with native aiohttp exception handling
- URL validation and RSS parsing functionality
- Integration tests for end-to-end workflows
- Edge case testing for malformed feeds and network failures
- Mock strategies for reliable testing without external dependencies
- Rate limiting and retry logic validation