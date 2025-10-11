# ContentNormalizer

## Purpose

- Enforce minimum content quality and standardize metadata before any AI processors run.

## Inputs

- Raw `Article` from fetchers (title, content, url, optional author/tags/published_at).
- `ContentNormalizationSettings` (see content section in `backend/docs/configuration.md`).
- AI provider for spam detection (optional override in tests).

## Outputs

- Returns normalized `Article` or `None` when the item should be dropped.
- Mutates in place: trims `content`, fixes `title`/`author`, deduplicates `tags`, normalizes `url`, enforces UTC `published_at`.
- Populates `article.metadata` with existing keys only; no new fields added yet.

## Dependencies

- PydanticAI spam agent via `ai_provider.create_ai_provider()` when `spam_detection_enabled` is true.
- Standard library helpers (`urllib.parse`) for URL cleanup.

## Hot Path / Algorithm

1. Content validation: reject empty/whitespace content, enforce `min_length`, optionally call spam agent.
2. If rejection occurs, log at DEBUG and return `None`.
3. Normalize `published_at`: fill from `fetch_timestamp` when missing, convert to UTC-aware datetime.
4. Cleanup metadata:
   - Title: collapse whitespace, truncate at word boundary, fallback to `"Untitled Article"`.
   - Author: trim, title-case, truncate.
   - Tags: lowercase, deduplicate, trim length, enforce `max_tags_per_article`.
   - URL: drop tracking params, upgrade http→https, rebuild canonical form.
5. Enforce `max_length` for `content` using word-boundary truncation.

## Failure Modes

- Shared behaviours: `backend/docs/processors/common_patterns.md`.
- Processor-specific:
  - Content below thresholds or flagged as spam → returns `None`.
  - Missing `published_at` → warns and substitutes `fetch_timestamp`.
  - Exceptions inside spam agent → treated as non-spam (so article continues).

## Metrics & Instrumentation

- No dedicated metrics; rely on DEBUG/INFO logs during validation.
- TODO (future): counters for rejected articles by reason.

## Settings

- `ContentNormalizationSettings.min_length`, `.max_length`, `.spam_detection_enabled`, `.title_max_length`, `.author_max_length`, `.tag_max_length`, `.max_tags_per_article`.

## Tests

- `backend/tests/test_processors/test_normalizer.py`.

## Changelog

- **2025-09-25**: Spam detection + metadata normalization hardened ahead of AI stages.
