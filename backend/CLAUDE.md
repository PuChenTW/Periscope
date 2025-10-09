# Personal Daily Reading Digest - Backend Development Guide

## Overview

This document provides comprehensive guidance for developing the backend systems of the Personal Daily Reading Digest platform. The backend is built using FastAPI with PostgreSQL, integrated with PydanticAI for content processing and Temporal for workflow orchestration.

## Documentation Structure

**Read the relevant docs based on what you're implementing:**

- @docs/architecture.md - System layers, project structure, API/Service/Repository patterns
- @docs/design-patterns.md - Repository pattern, dependency injection, error handling
- @docs/database-design.md - SQLAlchemy models, schemas, ULID mixins, relationships
- @docs/temporal-workflows.md - Workflows, activities, retries, fault tolerance
- @docs/content-processing.md - RSS feeds, AI providers, similarity detection, summarization
- @docs/configuration.md - Environment variables for all services (Database, Redis, AI, etc.)
- @docs/testing-strategy.md - Test structure, fixtures, mocks, coverage targets
- @docs/operations.md - Caching, monitoring, logging, security, performance

## Coding Guidelines

### String Formatting and Multi-line Text

**Always use `textwrap.dedent()` for multi-line strings**, especially for:
- AI prompts (system prompts, user prompts)
- SQL queries
- Error messages
- Documentation strings
- Configuration templates

This ensures proper formatting and prevents indentation issues that can affect AI model performance or code readability.

**Example - AI System Prompts:**
```python
import textwrap
from pydantic_ai import Agent

# ✅ GOOD: Clean, well-formatted prompt
agent = provider.create_agent(
    output_type=MyResult,
    system_prompt=textwrap.dedent("""\
        You are an expert at analyzing content.
        Your task is to identify key patterns.

        Guidelines:
        - Be specific and concise
        - Provide reasoning for your decisions
        - Use structured output format
    """),
)

# ❌ BAD: Awkward formatting, hard to read
agent = provider.create_agent(
    output_type=MyResult,
    system_prompt=(
        "You are an expert at analyzing content."
        "Your task is to identify key patterns."
        "Guidelines:"
        "- Be specific and concise"
        "- Provide reasoning for your decisions"
    ),
)
```

**Example - User Prompts:**
```python
# ✅ GOOD: Clean formatting with f-strings
prompt = textwrap.dedent(f"""\
    Article Title: {article.title}
    Content: {article.content}

    Analyze this article and provide insights.
""")

# ❌ BAD: Hard to read, no structure
prompt = f"Article Title: {article.title}\nContent: {article.content}\n\nAnalyze this article and provide insights."
```

**Why this matters:**
- AI models perform better with well-formatted, structured prompts
- Code is more readable and maintainable
- Easier to update and modify prompts
- Consistent formatting across the codebase
