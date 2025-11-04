# Personal Daily Reading Digest - Backend

![Static Badge](https://img.shields.io/badge/test%20coverage-81%25-brightgreen)

This is the Phase 1 MVP backend for the Personal Daily Reading Digest platform, built with FastAPI.

## Current Status

**Completed Phase 1+ Features:**

- Core FastAPI application structure
- Database models with SQLAlchemy (PostgreSQL ready)
- Memory-based caching layer (Redis-compatible interface)
- Mock API endpoints for authentication, user management, and digest operations
- **RSS Feed Fetching Layer** (✅ **COMPLETED**)
  - RSS/Atom feed parsing and validation
  - Simplified async HTTP client with streamlined retry logic and native aiohttp exception handling
  - Content extraction and metadata processing
  - Comprehensive test suite (73 tests passing)
- **AI Provider Abstraction** (✅ **COMPLETED**)
  - Pluggable AI model architecture for easy provider switching
  - Protocol-based design with GeminiProvider implementation
  - Configuration-driven model selection
  - Enhanced testability with dependency injection
- **Similarity Detection & Grouping Engine** (✅ **COMPLETED**)
  - AI-powered semantic analysis for detecting similar articles
  - Connected components algorithm for efficient grouping
  - Topic aggregation from grouped articles
  - Redis caching with 24-hour TTL
  - Comprehensive test suite (21 tests passing)
- **Topic Extraction Service** (✅ **COMPLETED**)
  - AI-powered key topic identification for articles
  - Structured output with Pydantic models
  - Configurable max topics limit (default: 5)
  - Article model enhanced with ai_topics field
  - Comprehensive test suite (19 tests passing)
- Docker development environment
- Basic testing setup
- Alembic migrations (ready for database setup)

## Architecture

```text
app/
   api/            # API endpoints and routes
   models/         # SQLAlchemy database models
   processors/     # Content processing engines (✅ COMPLETED)
      fetchers/    # RSS/Atom feed fetchers and factory
      utils/       # HTTP client and validation utilities
      ai_provider.py        # AI provider abstraction (✅ COMPLETED)
      similarity_detector.py # Similarity detection engine (✅ COMPLETED)
      topic_extractor.py    # Topic extraction service (✅ COMPLETED)
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
   - API: <http://localhost:8000>
   - Interactive docs: <http://localhost:8000/docs>
   - Health check: <http://localhost:8000/health>

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

## Testing Command

```bash
make test  # Run all tests
```

Current test coverage includes:

- API endpoint functionality
- Mock data validation
- Basic integration tests
- **Content Processing Engines** (~149 total processor tests)
  - RSS Feed Fetching Layer (73 tests)
  - Similarity Detection & Grouping (21 tests)
  - Topic Extraction Service (19 tests)
  - HTTP client, URL validation, and integration workflows

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

Phase 1+ provides complete content processing foundation. Phase 2 will add:

- Business service layer implementation
- AI-powered summarization and relevance scoring
- Temporal workflow implementation for digest generation
- Redis cache integration
- Email delivery service

## Environment Variables

Key configuration options:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SECRET_KEY=your-secret-key
DEBUG=true

# AI Provider Configuration
AI_PROVIDER=gemini                    # AI provider: gemini, openai (default: gemini)
GEMINI_API_KEY=your-gemini-api-key   # Google Gemini API key
GEMINI_MODEL=gemini-2.5-flash-lite   # Gemini model name

# Email Configuration
EMAIL_PROVIDER=smtp
SMTP_HOST=localhost

# Cache Configuration
CACHE_TTL_MINUTES=60

# Similarity Detection Settings
SIMILARITY_THRESHOLD=0.7             # Minimum confidence for similar articles
SIMILARITY_CACHE_TTL_MINUTES=1440    # Cache TTL for similarity results (24h)

# Topic Extraction Settings
TOPIC_EXTRACTION_MAX_TOPICS=5       # Maximum topics to extract per article
```

## API Documentation

Interactive API documentation is available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

All endpoints return JSON and include proper OpenAPI specifications with request/response models.

## Content Processing Pipeline

The content processing layer provides comprehensive RSS fetching, AI-powered analysis, and intelligent article grouping:

### RSS Feed Fetching

- Support for RSS 2.0 and Atom 1.0 feeds
- Simplified async HTTP client with retry logic and native aiohttp exception handling
- HTML content cleaning and text normalization
- Comprehensive test suite (73 tests)

### AI-Powered Processing

**Topic Extraction Service:**

- Identifies 3-5 key topics/themes from article content
- Uses configurable AI providers (Gemini by default)
- Stores topics in Article.ai_topics field for downstream processing
- Graceful error handling with fallback to empty list

**Similarity Detection & Grouping:**

- Semantic analysis to detect similar articles from different sources
- Connected components algorithm for efficient grouping
- Aggregates topics from all articles in each group
- Redis caching (24-hour TTL) to avoid redundant AI calls
- Configurable similarity threshold (default: 0.7)

### Testing Coverage

Comprehensive test suite with ~149 total processor tests covering:

- HTTP client, URL validation, and RSS parsing (73 tests)
- Similarity detection and grouping logic (21 tests)
- Topic extraction and content analysis (19 tests)
- Integration workflows and edge cases
- Mock AI providers for deterministic testing
