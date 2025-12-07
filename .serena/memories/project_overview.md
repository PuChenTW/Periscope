# Periscope - Personal Daily Reading Digest

## Project Purpose

A content curation platform that automatically aggregates, summarizes, and delivers personalized daily email digests from preferred news sources, blogs, and publications.

## Tech Stack

### Backend

- **Python**: 3.13+
- **FastAPI**: High-performance web framework with automatic API documentation
- **PostgreSQL**: Relational database for user data and configuration
- **Redis**: Caching layer for temporary storage and session management
- **SQLModel**: ORM combining SQLAlchemy with Pydantic
- **Temporal**: Workflow orchestration for content processing pipelines
- **PydanticAI**: AI framework for content summarization and processing
- **aiohttp**: Async HTTP client for feed fetching
- **feedparser**: RSS/Atom feed parsing
- **BeautifulSoup4**: HTML content extraction and cleaning
- **Alembic**: Database migration management

### Frontend

- **Vite**: Modern build tool
- **Svelte**: Lightweight reactive framework

### Development Tools

- **UV**: Python package manager
- **Pytest**: Testing framework with asyncio and xdist support
- **Ruff**: Code formatter and linter
- **MyPy**: Type checking
- **Docker & Docker Compose**: Containerization

## Current Completion (as of 2025-12-01)

### Phase 1 MVP - Critical Blockers Status
- ✅ **User management APIs**: User registration, auth, source CRUD fully implemented with persistence
- ✅ **Content fetching activity**: `fetch_content_activity` implemented with parallel source fetching
- 🟡 **Email delivery**: Service structure ready (SMTP/Brevo support), mock sender active, needs real integration

### Phase 1-2 Features
- ✅ **Personalization pipeline**: All 4 batch activities (normalize, quality, topics, relevance) complete with 15 tests
- ✅ **Summarization & similarity**: Processors complete (21 tests), fully integrated into Temporal workflow
- ✅ **Temporal Core Pipeline**: `daily_digest` workflow implemented with 11-step pipeline (fetch -> validate -> normalize -> quality -> topics -> relevance -> summary -> similarity -> assemble)
- ⏳ **Delivery scheduling**: Temporal cron setup pending

### Testing & Quality
- 🟡 **E2E tests**: Workflow activity tests passing, needs user registration → config → digest generation flow test
- 🟡 **API integration**: User APIs tested, needs full integration test suite
- Content Processing Engines: RSS fetching (73 tests), similarity detection (21 tests), topic extraction (19 tests)
- Overall test coverage: 81%+

## Completed Implementations (Phase 1-4)

### User & Authentication
- User model with email verification and preferences
- UserRepository for CRUD operations
- Authentication endpoints (register, login, verify)
- User configuration endpoints (sources, preferences)

### Content Processing Activities
- **FetchContentActivity**: Parallel RSS source fetching with error handling
- **ProcessingActivities**: Batch processing for normalize, quality, topics, relevance scoring
- **SummarizeArticlesActivity**: AI-powered article summarization
- **DetectSimilarArticlesActivity**: Semantic similarity detection (21 tests)
- **AssemblyActivities**: Digest assembly with grouped articles

### Email & Delivery
- EmailService with SMTP/Brevo support (mock sender active)
- DigestAssemblyActivity for final digest composition
- Email templates structure ready

## Key Modules

### Core Application

- `app/main.py`: FastAPI application factory
- `app/config.py`: Configuration management
- `app/database.py`: Database connection setup

### Content Processing (`app/processors/`)

- **RSS Fetching**: RSS 2.0 and Atom 1.0 feed parsing
- **Similarity Detection**: AI-powered semantic analysis for grouping similar articles
- **Topic Extraction**: Extract key topics from articles using AI

### API & Services

- `app/api/`: FastAPI route handlers
- `app/services/`: Business logic layer
- `app/repositories/`: Data access layer

### Models & Database

- `app/models/`: SQLAlchemy database models
- `alembic/`: Database migrations

### Temporal Workflows

- `app/temporal/`: Workflow and activity definitions for batch processing (Core pipeline implemented)

## Project Architecture Notes

- Functional-first approach preferred over classes where possible
- Return early to avoid deep nesting
- Pure functions with composition
- Comprehensive error handling with domain-specific exceptions
- Google-style docstrings required
- Maximum line length: 120 characters
