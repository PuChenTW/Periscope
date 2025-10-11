# Configuration Guide

## Quick Start

- Load settings via `from app.config import get_settings`; cache the result, do not re-read env per call.
- Environment variables use double underscores: `GROUP__FIELD` → `settings.group.field`.
- Add a new variable? document it here, provide default, update `.env.example`.

```python
from app.config import get_settings

settings = get_settings()
database_url = settings.database.url          # DATABASE__URL
ai_provider = settings.ai.provider            # AI__PROVIDER
gemini_model = settings.ai.gemini_model       # AI__GEMINI_MODEL
```

## Settings Groups

| Group Attr | Env Prefix | Purpose |
| --- | --- | --- |
| `database` | `DATABASE__` | Postgres connection + options. |
| `redis` | `REDIS__` | Redis cache connection + pool sizing. |
| `cache` | `CACHE__` | Default cache TTLs. |
| `email` | `EMAIL__` | SMTP / provider credentials. |
| `ai` | `AI__` | Provider + model selection. |
| `rss` | `RSS__` | Fetcher/network tuning. |
| `similarity` | `SIMILARITY__` | Graph threshold + cache. |
| `topic_extraction` | `TOPIC_EXTRACTION__` | Topic limits. |
| `summarization` | `SUMMARIZATION__` | Summary length + truncation. |
| `custom_prompt` | `CUSTOM_PROMPT__` | User prompt bounds. |
| `ai_validation` | `AI_VALIDATION__` | Prompt validation controls. |
| `content` | `CONTENT__` | Normalizer limits + spam toggles. |
| `personalization` | `PERSONALIZATION__` | Relevance scoring weights. |
| `security` | `SECURITY__` | JWT + auth secrets. |

## Required Variables

| Setting | Default | Why |
| --- | --- | --- |
| `DATABASE__URL` | — | Without it the app refuses to boot. |
| `SECURITY__SECRET_KEY` | — | JWT signing. |
| `EMAIL__PROVIDER` | `smtp` | Required even if mocked; controls email strategy. |

## Database & Cache

| Setting | Default | Purpose / Notes |
| --- | --- | --- |
| `DATABASE__URL` | (none) | Full SQLAlchemy URL; include `?sslmode=` for cloud envs. |
| `REDIS__URL` | `redis://localhost:6379/0` | Shared cache + processor memoization. |
| `REDIS__MAX_CONNECTIONS` | `10` | Tune up only after profiling. |
| `CACHE__TTL_MINUTES` | `60` | Baseline TTL for generic cache helpers. |

## Email

| Setting | Default | Notes |
| --- | --- | --- |
| `EMAIL__PROVIDER` | `smtp` | Supported: `smtp`, `sendgrid`, `ses`. |
| `EMAIL__API_KEY` | `""` | Required for non-SMTP providers. |
| `EMAIL__SMTP_HOST` | `localhost` | Only used when provider=`smtp`. |
| `EMAIL__SMTP_PORT` | `587` | Must match infra; prefer STARTTLS. |
| `EMAIL__SMTP_USERNAME` | `""` | Leave blank for unauthenticated local dev. |
| `EMAIL__SMTP_PASSWORD` | `""` | Never log this. |

## AI & Fetching

| Setting | Default | Notes |
| --- | --- | --- |
| `AI__PROVIDER` | `gemini` | Wire to provider factory; see `processors/ai_provider.py`. |
| `AI__GEMINI_API_KEY` | `""` | Required when provider=`gemini`. |
| `AI__GEMINI_MODEL` | `gemini-2.5-flash-lite` | Override to control latency/cost. |
| `AI__OPENAI_API_KEY` | `""` | Placeholder for future. |
| `AI__OPENAI_MODEL` | `gpt-5-nano` | Placeholder. |
| `RSS__FETCH_TIMEOUT` | `30` | Seconds per request. |
| `RSS__MAX_RETRIES` | `3` | Applied with fixed backoff (`RSS__RETRY_DELAY`). |
| `RSS__RETRY_DELAY` | `1.0` | Seconds between retries. |
| `RSS__MAX_ARTICLES_PER_FEED` | `100` | Hard cap to protect memory. |
| `RSS__USER_AGENT` | `Periscope-Bot/1.0 (+https://periscope.ai/bot)` | Respect robots.txt. |

## Processor Settings Snapshot

| Processor | Settings Object | Key Fields |
| --- | --- | --- |
| SimilarityDetector | `SimilaritySettings` | `threshold`, `cache_ttl_minutes`, `batch_size`. |
| TopicExtractor | `TopicExtractionSettings` | `max_topics`. |
| Summarizer | `SummarizationSettings` | `max_length`, `content_length`. |
| Custom Prompt Validator | `CustomPromptSettings` | `min_length`, `max_length`, `validation_enabled`. |
| AI Prompt Validation | `AIPromptValidationSettings` | `enabled`, `threshold`, `cache_ttl_minutes`. |
| ContentNormalizer | `ContentNormalizationSettings` | Content length bounds, spam toggle, tag limits. |
| QualityScorer | `ContentNormalizationSettings.quality_scoring_enabled` | Toggles AI path. |
| RelevanceScorer | `PersonalizationSettings` | Keyword weights, relevance threshold, boost factor, cache ttl, semantic toggle. |

Each processor receives **only** the settings object it needs. Pass custom instances in tests to avoid loading the full settings tree.

## Personalization Extras

| Setting | Default | Behaviour |
| --- | --- | --- |
| `PERSONALIZATION__KEYWORD_WEIGHT_TITLE` | `3` | Title match weight. |
| `PERSONALIZATION__KEYWORD_WEIGHT_CONTENT` | `2` | Body match weight. |
| `PERSONALIZATION__KEYWORD_WEIGHT_TAGS` | `4` | Tag/topic match weight. |
| `PERSONALIZATION__MAX_KEYWORDS` | `50` | Enforced on profile save. |
| `PERSONALIZATION__RELEVANCE_THRESHOLD_DEFAULT` | `40` | Fallback threshold when profile unset. |
| `PERSONALIZATION__BOOST_FACTOR_DEFAULT` | `1.0` | Multiplier applied post-score; clamp 0.5–2.0. |
| `PERSONALIZATION__CACHE_TTL_MINUTES` | `720` | Redis memoization for `(profile, article)` pairs. |
| `PERSONALIZATION__ENABLE_SEMANTIC_SCORING` | `true` | Gates AI semantic lift stage. |

## Override Order

1. Environment variables
2. `.env` (committed template)
3. `.env.local` (ignored; personal overrides)
4. Defaults in `config.py`

Production must use environment variables only. Secrets belong in your secrets manager, not `.env`.

## Validation Rules

- Application fails fast on missing required settings; do not guard with try/except.
- Numeric fields validated for range (see dataclasses in `config.py`).
- Add tests in `tests/unit/config` when introducing new constraints.

## Checklist for New Settings

- [ ] Add type + default to `app/config.py`.
- [ ] Document in this file (table + notes).
- [ ] Update `.env.example`.
- [ ] Ensure related processor doc references the new setting.
- [ ] Provide migration plan if required in deployment scripts.
