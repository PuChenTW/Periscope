# Fetchers

## Purpose

- Pull raw articles from configured sources and convert them into `Article` objects for the pipeline.

## Inputs

- Source URL string supplied by user configuration.
- `RSSSettings` for timeout/retry/article caps (see fetching section in `backend/docs/configuration.md`).
- Optional overrides for `timeout`/`max_articles` when constructing fetchers programmatically.

## Outputs

- `FetchResult` containing `source_info`, `articles`, `fetch_timestamp`, `success`, `error_message`.
- Each `Article` includes `title`, `url`, `content`, `published_at`, `fetch_timestamp`, optional `author`, `tags`, and empty AI fields.

## Dependencies

- `HTTPClient` async helper for network I/O (wraps aiohttp with timeout handling).
- `feedparser` for RSS/Atom parsing.
- `FetcherRegistry` / `auto_create_fetcher` exposed via `app.processors.fetchers.factory`.

## Hot Path / Algorithm

1. `detect_source_type(url)` inspects URL hints (rss/feed/atom) → defaults to RSS; raises `InvalidUrlError` on malformed URLs.
2. `create_fetcher`/`auto_create_fetcher` instantiates the registered class (currently `RSSFetcher`).
3. `validate_url` optionally pre-checks feed accessibility (`validate_rss_feed`).
4. `fetch_content`:
   - Rejects immediately on invalid URL format (returns `success=False` result).
   - Uses `HTTPClient` to download content with timeout/retry policy.
   - Parses feed; when empty, returns `success=False` with reason.
   - Converts entries to `Article` objects, cleaning HTML, inferring published dates, authors, tags.
5. `get_source_info` re-parses feed to populate `SourceInfo` (title, description, language, metadata).

## Failure Modes

- Shared behaviours: `backend/docs/processors/common_patterns.md`.
- Processor-specific:
  - Network timeout → `success=False`, `error_message="Request timeout"`.
  - Invalid URL → immediate `FetchResult` failure (no exception bubbles).
  - Malformed entries → skipped with WARN log; processing continues for remaining entries.

## Metrics & Instrumentation

- Log coverage only (timeouts, parse errors, entry skips).
- Future consideration: counter for `fetch.success` / `fetch.failure` per source.

## Settings

- `RSSSettings.fetch_timeout`, `.max_retries`, `.retry_delay`, `.max_articles_per_feed`, `.user_agent`.

## Tests

- `backend/tests/test_processors/test_fetchers/test_rss.py`.
- `backend/tests/test_processors/test_fetchers/test_factory.py`.

## Changelog

- **2025-09-25**: RSS fetcher + registry/factory shipped with validation and timeout handling.
