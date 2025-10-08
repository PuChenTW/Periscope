# Personal Daily Reading Digest - Backend Development Guide

## Overview

This document provides comprehensive guidance for developing the backend systems of the Personal Daily Reading Digest platform. The backend is built using FastAPI with PostgreSQL, integrated with PydanticAI for content processing and Temporal for workflow orchestration.

## Documentation Structure

Detailed architecture and design documentation has been organized into separate files for better maintainability:

@docs/architecture.md
@docs/design-patterns.md
@docs/database-design.md
@docs/temporal-workflows.md
@docs/content-processing.md
@docs/configuration.md
@docs/testing-strategy.md
@docs/operations.md

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
