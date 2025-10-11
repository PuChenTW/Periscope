# Summarizer

## Purpose

- Generate digest-friendly summaries for each article in the user’s preferred style (brief, detailed, bullet).

## Inputs

- `Article` enriched with topics (`article.ai_topics`) and optional `article.summary` (for reuse).
- `SummarizationSettings`, `CustomPromptSettings`, `AIPromptValidationSettings`.
- User preference: `summary_style` (`brief`, `detailed`, `bullet_points`).

## Outputs

- `article.summary` populated with formatted text.
- `article.metadata["summary_style"]` reflecting style used.

## Dependencies

- AI provider from `ai_provider.create_ai_provider()`.
- `textwrap.dedent` prompt templates located in `app/processors/summarizer.py`.
- Redis caching not yet wired (future enhancement noted).
- Settings reference: see summarization/prompt sections in `backend/docs/configuration.md`.

## Algorithm

1. Short-circuit: if content < `min_length_for_ai` (hard-coded), return excerpt without AI call.
2. Build system + user prompts (style-specific) with title, topics, tags, key metadata.
3. Call AI provider; validate output matches expected schema.
4. On success, format summary according to style, store in article.
5. On failure, log warning and fall back to first N characters (configurable) as excerpt.

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

- **2025-10-10**: Multi-style summarizer landed with AI fallback hierarchy.
