# Backend Workstream Status

**Legend:** 🟢 Complete | 🟡 In Progress | ⏳ Pending | ⚠️ Blocked

**See also:** [project_overview.md](project_overview.md) for phase-level status, [feature_matrix.md](feature_matrix.md) for feature status, [technical_debt.md](technical_debt.md) for full issue list

---

## CRITICAL BLOCKERS (Phase 1 MVP)

| Workstream | Owner | Status | Next Action | Priority | Updated |
| --- | --- | --- | --- | --- | --- |
| Content fetching activity | TBD | 🟢 Complete | `fetch_content_activity` implemented with parallel source fetching, error handling, and mock user configuration. 73 processor tests + activity tests passing. | P0 | 2025-12-01 |
| Email delivery implementation | TBD | 🟡 In Progress | Email service structure implemented (SMTP/Brevo support). Mock email sender active. Need real integration testing. Digest assembly activities complete. | P0 | 2025-12-01 |
| User management APIs | TBD | 🟢 Complete | User registration, auth, source CRUD endpoints fully implemented with database persistence and validation. Ready for integration testing. | P0 | 2025-12-01 |

---

## HIGH-PRIORITY FEATURES (Phase 1-2)

| Workstream | Owner | Status | Next Action | Priority | Updated |
| --- | --- | --- | --- | --- | --- |
| Personalization pipeline integration | TBD | 🟢 Complete (Phase 4) | All 4 batch activities implemented (normalize, quality, topics, relevance) with ProcessingActivities class. Workflow integration complete. 15 tests passing. Optional: add E2E chain test for full processor→activity pipeline. | P1 | 2025-10-21 |
| Summarization & similarity batch activities | TBD | 🟡 In Progress | Processors complete (summarization + similarity detection with 21 tests). Activities implemented in ProcessingActivities. Workflow integration in progress. | P1 | 2025-12-01 |
| Delivery scheduling (Temporal cron) | TBD | ⏳ Pending | Set up Temporal cron workflow for daily digest scheduling. Handle timezone conversion and 30-minute delivery window. Depends on user auth. | P1 | 2025-10-21 |

---

## TESTING & QUALITY ASSURANCE

| Workstream | Owner | Status | Next Action | Priority | Updated |
| --- | --- | --- | --- | --- | --- |
| E2E integration tests | TBD | 🟡 In Progress | Integration test infrastructure established. Tests for workflow activities (content fetching, assembly) passing. Need: user registration → source config → digest generation flow test. | P1 | 2025-12-01 |
| API integration tests | TBD | 🟡 In Progress | User APIs fully implemented and tested. Source management endpoints complete. Need: full integration test suite with FastAPI TestClient. | P1 | 2025-12-01 |
| Additional activity tests | TBD | ⏳ Partial | Add tests for quality/topics batch activities and full processor chain. Core implementation complete. | P2 | 2025-10-21 |

---

## OPTIMIZATION & IMPROVEMENTS

| Workstream | Owner | Status | Next Action | Priority | Updated |
| --- | --- | --- | --- | --- | --- |
| Processor telemetry & metrics | TBD | ⏳ Pending | Select metrics sink (Prometheus/CloudWatch/Datadog) and dashboards. Observability fields instrumented in code, need sink. | P2 | 2025-10-21 |
| Blog fetcher (non-RSS sources) | TBD | ⏳ Pending | Implement blog/URL fetcher processor for non-RSS content sources. Documented but not implemented. Low priority (Phase 3 feature). | P2 | 2025-10-21 |
| Quality scorer caching | TBD | ⏳ Pending | Add Redis memoization layer for quality scores (already done for spam/topics/relevance). Optional optimization. | P3 | 2025-10-21 |
| Summarizer result caching | TBD | ⏳ Pending | Cache summary results to avoid recomputation for similar content. Optional optimization. | P3 | 2025-10-21 |

---

## INFRASTRUCTURE & OPERATIONS

| Workstream | Owner | Status | Next Action | Priority | Updated |
| --- | --- | --- | --- | --- | --- |
| Workflow observability | TBD | 🟡 In Progress | Add Temporal alerting, integrate with metrics sink, document dashboards in operations guide. Depends on metrics sink selection. | P2 | 2025-10-21 |
| Soft delete support | TBD | ⏳ Pending | Introduce `deleted_at` columns to models, update repositories to filter soft-deleted items. Nice-to-have (Phase 4+). | P3 | 2025-10-21 |
| Database migrations (Alembic) | TBD | ⏳ Pending | Set up migration system for schema version control. Currently using SQLModel directly. Phase 5 readiness. | P3 | 2025-10-21 |
| Production deployment runbook | TBD | ❌ Not started | Document environment setup, health checks, troubleshooting, rollback procedures. Phase 5 requirement. | P3 | 2025-10-21 |

---

## LOWER-PRIORITY METRICS

| Workstream | Owner | Status | Next Action | Priority | Updated |
| --- | --- | --- | --- | --- | --- |
| Normalizer rejection metrics | TBD | ⏳ Pending | Emit counters for article rejection reasons. Requires metrics sink. | P3 | 2025-10-21 |
| Similarity batching optimization | TBD | ⏳ Pending | Honor `SimilaritySettings.batch_size` to reduce pairwise comparisons. Performance optimization. | P3 | 2025-10-21 |
| Fetcher success metrics | TBD | ⏳ Pending | Add success/failure counters per RSS source. Requires metrics sink. | P3 | 2025-10-21 |
