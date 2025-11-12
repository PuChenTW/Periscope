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

## Current Completion

- Phase 1+ MVP: Core application structure, database models, API endpoints
- Content Processing Engines: RSS fetching (73 tests), similarity detection (21 tests), topic extraction (19 tests)
- 81% test coverage

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

- `app/temporal/`: Workflow and activity definitions for batch processing

## Project Architecture Notes

- Functional-first approach preferred over classes where possible
- Return early to avoid deep nesting
- Pure functions with composition
- Comprehensive error handling with domain-specific exceptions
- Google-style docstrings required
- Maximum line length: 120 characters
