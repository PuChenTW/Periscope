# Temporal Workflow Playbook

## Non-Negotiables

- **Idempotent activities**: check existing state before writes; safe to replay after retry.
- **Deterministic inputs**: no random/time-based decisions inside workflows; pass timestamps from activities.
- **Tight timeouts**: every activity declares a timeout class (fast/medium/long) in code + table below.
- **Structured errors**: raise domain errors (`ExternalServiceError`, `ValidationError`) so retry policies can react.

## Core Workflows

| Workflow | Purpose | Key Activities | Notes |
| --- | --- | --- | --- |
| `daily_digest` (In Progress) | Orchestrate daily content → email. | `fetch_user_config`, `fetch_sources_parallel`, `validate_and_filter_batch`, `normalize_articles_batch`, `score_quality_batch`, `extract_topics_batch`, `score_relevance_batch`, `summarize_articles_batch`, `detect_similar_articles_batch`, `assemble_digest`, `send_email` (mock). | Core orchestration logic implemented in `workflows.py`. |
| `user_onboarding` (planned) | Validate new user config + email verification. | `validate_sources`, `send_verification_email`, `await_verification`, `activate_user`. | Workflow queue stub still pending; `await_verification` will use Temporal signals with 48h timeout. |
| `source_validation` (planned) | Asynchronous source health checks. | `fetch_source_probe`, `update_validation_status`. | Triggered on demand or via cron schedule once Temporal infra exists. |

## Activity Matrix

| Activity | Owner Module | Timeout Class | Retries | Idempotency Check |
| --- | --- | --- | --- | --- |
| `fetch_user_config` ✅ | `app/temporal/activities/content.py:32` | Fast (<5s) | 3 attempts, backoff 2s → 10s | Single DB read; no side effects. |
| `fetch_sources_parallel` ✅ | `app/temporal/activities/content.py:116` | Medium (30s) | 3 attempts, backoff 5s → 45s | No cache needed; transient raw content. Idempotent via fetch timestamp in Article model. |
| `validate_and_filter_batch` ✅ | `app/temporal/activities/processing.py` | Medium (30s) | 3 attempts, backoff 5s → 45s | Basic validation + AI spam detection. |
| `normalize_articles_batch` ✅ | `app/temporal/activities/processing.py:109` | Medium (30s) | 3 attempts, backoff 5s → 45s | Cache key: `spam:{sha256(title+content[:1000])[:16]}`. Caches spam detection results. TTL: 1440 min. |
| `score_quality_batch` ✅ | `app/temporal/activities/processing.py:201` | Long (120s) | 2 attempts, backoff 15s → 120s | Cache key: `quality:{sha256(url)[:16]}`. Stores hybrid quality scores. TTL: 720 min. |
| `extract_topics_batch` ✅ | `app/temporal/activities/processing.py:296` | Long (120s) | 2 attempts, backoff 15s → 120s | Cache key: `topics:{sha256(url)[:16]}`. Caches AI-extracted topics. TTL: 1440 min. |
| `score_relevance_batch` ✅ | `app/temporal/activities/processing.py:399` | Medium (30s) | 3 attempts, backoff 5s → 45s | Cache key: `relevance:{profile_hash}:{article_url}`. Profile hash includes keywords, threshold, boost_factor. TTL: 720 min. |
| `summarize_articles_batch` ✅ | `app/temporal/activities/processing.py` | Long (120s) | 2 attempts, backoff 15s → 120s | Uses AI cache; stores neutral summary on failure. |
| `detect_similar_articles_batch` ✅ | `app/temporal/activities/processing.py` | Long (120s) | 2 attempts, backoff 15s → 120s | Semantic similarity detection. |
| `assemble_digest` ✅ | `app/temporal/activities/digest.py` (or similar) | Fast | 1 attempt (no retry) | Pure data shaping. |
| `send_email` (planned) | `app/temporal/activities/email.py` (pending module) | Medium | 4 attempts, backoff 10s → 2m | Email provider idempotency key = digest ULID + attempt. |
| `record_delivery` (planned) | `app/temporal/activities/status.py` (pending module) | Fast | 3 attempts | UPSERT on delivery status table keyed by (user_id, delivery_date). |

_Timeout classes align with `temporalio.activity.ActivityOptions` declared in code. Update both table and code together._

## Retry & Failure Policy

- Use exponential backoff with jitter disabled (determinism). Cap retry attempts per table above.
- Mark errors from external providers as retryable; mark validation errors as non-retryable.
- Always emit a workflow metric (`workflow.failure_reason`) before propagating fatal errors.
- For partial failures (e.g., some sources dead), record the issue in delivery metadata and continue.

## Integration Checklist

- Adding an activity? Append it to the matrix, define timeout/retry in code, and document cache keys in `operations.md`.
- Introducing a new workflow? Provide purpose + activity list here, add monitoring entry in `operations.md`, and wire schedule/trigger.
- Changing processor order? Reflect in `daily_digest` row and ensure corresponding processor docs highlight dependency.

## Debugging Tips

- Temporal UI: filter by workflow type; inspect activity history for retry counts.
- Logging: every activity should log start + end with correlation ID (`workflow_id/activity_name`).
- Replay issues usually mean non-deterministic code—check for datetime.now(), random, or unordered iteration in workflow functions.
