# Personal Daily Reading Digest - Backend

This is the Phase 1 MVP backend for the Personal Daily Reading Digest platform, built with FastAPI.

## Current Status

**Completed Phase 1 MVP Features:**
- Core FastAPI application structure
- Database models with SQLAlchemy (PostgreSQL ready)
- Memory-based caching layer (Redis-compatible interface)
- Mock API endpoints for authentication, user management, and digest operations
- Docker development environment
- Basic testing setup
- Alembic migrations (ready for database setup)

## Architecture

```
app/
   api/            # API endpoints and routes
   models/         # SQLAlchemy database models
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

Phase 1 provides the foundation. Phase 2 will add:
- Real authentication with JWT
- Business service layer implementation
- RSS feed fetching and content processing
- AI integration with PydanticAI
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