# Operations Cheat Sheet

## Caching

| Namespace | Key Pattern | TTL | Notes / Invalidations |
| --- | --- | --- | --- |
| User config | `config:user:{user_id}` | 60 min | Bust on config update or source change. |
| Raw articles | `content:raw:{source_id}:{date}` | 24 h | Set by fetchers; reuse when fetch fails. |
| Processor memo | `processor:{name}:{article_digest}` | varies (see settings) | Used by Normalizer, Similarity, Relevance, Summarizer. Respect hashes. |
| API responses | `api:response:{endpoint}:{params_hash}` | 5–15 min | Only for idempotent GETs. |

- Key format: `periscope:{namespace}:...`. Do not invent new root namespaces without adding them here.
- Cache helpers live in `app/utils/cache.py`. Always pass an explicit TTL.

## Monitoring & Metrics

| Area | Metric | Target / Alert |
| --- | --- | --- |
| API | `http_latency_seconds{quantile="0.95"}` | < 250 ms; page if > 500 ms 3m+ |
| API | `http_error_total{status=~"5.."}` | 0 tolerance; alert on > 5/min. |
| Temporal | `workflow_duration_seconds{workflow="daily_digest"}` | < 15 min; warn at 12 min. |
| Temporal | `activity_retry_total` | Investigate spikes; log offending activity. |
| Fetchers | `rss_fetch_success_ratio` | Keep ≥ 0.95 per 24h. |
| AI | `ai_call_latency_seconds` | Track p95 < 2s; alert if >5s. |
| Email | `email_send_failure_total` | Retry path already covers; alert if >3 consecutive failures. |

- Export metrics via Prometheus; dashboards live in Grafana (link TBD).
- Before adding a new metric, decide alert policy; document it here.

## Logging

- Structured logging via Loguru; JSON output for files, human-readable for console.
- Minimum fields: `timestamp`, `level`, `message`, `request_id`, `workflow_id` (if Temporal), `user_id` (when authenticated).
- Rotate logs daily or at 100 MB; keep 30 days compressed.
- Never log secrets, tokens, or raw article content > 2 KB.

## Security Checklist

| Concern | Action |
| --- | --- |
| JWT | `SECURITY__SECRET_KEY` must be 32+ bytes. Rotate yearly. |
| Rate limiting | Enforce via middleware (per-user + IP). Document overrides. |
| External fetch | Validate scheme (http/https), block internal IP ranges, obey `robots.txt`. |
| Content sanitization | Strip scripts/tags in Normalizer; maintain allowlist in processor doc. |
| Secrets | Only via env/secret manager; never in git. |
| Headers | Ensure FastAPI middleware sets HSTS, X-Frame-Options=DENY, X-Content-Type-Options=nosniff, CSP (default strict). |

## Performance Tips

- Profile before tuning. Use `uv run python -m cProfile` or Pyinstrument on slow endpoints.
- Batch DB reads/writes; avoid per-article commits inside workflows.
- Push work off the request thread: schedule Temporal workflow, return 202 when applicable.
- Cache AI work aggressively; bail out early on obviously low-scoring content to skip AI calls.

## Runbooks

- **Temporal incident**: Check Temporal UI → identify failing activity → inspect logs with same `workflow_id` → apply retry/patch. Update `status_board.md` if prolonged.
- **RSS outages**: Failing source? Mark inactive via configuration service, keep digest delivery alive, record issue in user delivery metadata.
- **AI provider degraded**: Flip `PERSONALIZATION__ENABLE_SEMANTIC_SCORING=false` or equivalent summarizer toggle; processors must gracefully degrade (see processor docs).

Keep this sheet tight. When you add a new cache, metric, or security control, log it here immediately.
