# TopicExtractor

## Purpose

- Extract concise topical labels from article content so downstream ranking and summarization can reuse them.

## Inputs

- `Article` with normalized `title`, `content`, optional `tags`.
- `TopicExtractionSettings` (see topic section in `backend/docs/configuration.md`).
- AI provider instance (defaults to `create_ai_provider(get_settings())` if not injected).

## Outputs

- Returns `list[str]` of topics; callers assign to `article.ai_topics`.
- Debug logs include reasoning text for traceability.

## Dependencies

- PydanticAI agent created through `ai_provider.create_ai_provider()`.
- Settings control `max_topics`; no internal caching yet.

## Hot Path / Algorithm

1. Reject articles with <50 meaningful characters to avoid low-signal calls.
2. Build prompt with title, first 1000 chars of content, and tags (when present).
3. Call PydanticAI agent; enforce `max_topics` cap on the returned list.
4. Log topics + reasoning; return list to caller.

## Failure Modes

- Shared behaviours: `backend/docs/processors/common_patterns.md`.
- Processor-specific:
  - Empty/short content → return `[]` without invoking AI.
  - AI exception → log error and return `[]` (callers treat as “no topics”).

## Metrics & Instrumentation

- No dedicated metrics yet; relies on log sampling for monitoring.

## Settings

- `TopicExtractionSettings.max_topics` governs list truncation (see configuration guide).

## Tests

- `backend/tests/test_processors/test_topic_extractor.py`.

## Changelog

- **2025-10-10**: PydanticAI-backed topic extraction rolled into the default pipeline.
