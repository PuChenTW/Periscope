# Summarizer

## Purpose

- Generate digest-friendly summaries for each article in the user’s preferred style (brief, detailed, bullet).

## Inputs

- `Article` with: `title`, `content`, `tags`.
- `topics: list[str] | None` (optional dependency from TopicExtractor for enhanced context).
- `SummarizationSettings`, `CustomPromptSettings`, `AIPromptValidationSettings`.
- User preference: `summary_style` (`brief`, `detailed`, `bullet_points`).
- Optional `custom_prompt: str` (user-defined prompt validated for safety).

## Outputs

Returns `SummaryResult` with:

- `summary: str` (formatted summary text, style-specific)
- `key_points: list[str]` (3-5 key takeaways from article)
- `reasoning: str` (explanation of summarization approach)

**Note**: Does not mutate input article. Accepts `topics` as parameter for dependency injection.

## Dependencies

- AI provider from `ai_provider.create_ai_provider()`.
- `textwrap.dedent` prompt templates located in `app/processors/summarizer.py`.
- Redis caching not yet wired (future enhancement noted).
- Settings reference: see summarization/prompt sections in `backend/docs/configuration.md`.

## Algorithm

1. **Lazy initialization**: Validate and sanitize custom prompt on first use (`prepare()` method).
2. **Short-circuit**: If content < 100 chars, return excerpt without AI call (returns `SummaryResult` with fallback).
3. **Prompt building**: Construct prompt with title, tags, topics (from parameter or article.ai_topics), and truncated content.
4. **AI call**: Invoke agent with style-specific system prompt + user preferences.
5. **Formatting**: Apply style-specific formatting:
   - `brief`/`detailed`: Return summary text as-is
   - `bullet_points`: Format key_points as bullet list, prepend to summary
6. **Error handling**: On AI failure, fall back to excerpt (first 300 chars) with error reasoning.
7. Return `SummaryResult` with summary, key_points, and reasoning.

## Failure Modes

- Shared behaviours: `backend/docs/processors/common_patterns.md`.
- Additional specifics:
  - Empty/short content → return excerpt without AI call (DEBUG).
  - Unsupported style (should be caught by validation) → raises `ValueError`, caller falls back (ERROR).

## Metrics & Instrumentation

- Planned metric: `summary.ai_calls_total` with labels `{style}`.
- Track fallback frequency via `summary.fallback_total`.

## Tests

- `backend/tests/test_processors/test_summarizer.py` (styles, fallbacks, prompt validation).

## Changelog

- **2025-10-12**: Refactored to return `SummaryResult` and accept `topics` as parameter for dependency injection.
- **2025-10-10**: Multi-style summarizer landed with AI fallback hierarchy.
