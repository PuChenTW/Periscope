# Backend Workstream Status

Legend: 🟢 Complete | 🟡 In Progress | ⏳ Pending | ⚠️ Blocked

| Workstream | Owner | Status | Next Action | Updated |
| --- | --- | --- | --- | --- |
| Personalization pipeline integration | TBD | 🟡 In Progress | Implement `score_relevance_batch` activity with RelevanceScorer integration and cache-based idempotency (Phase 2-3). | 2025-10-12 |
| Processor telemetry & metrics | TBD | ⏳ Pending | Select metrics sink + dashboards; instrument processors once sink is ready. | 2025-10-11 |
| Digest assembly enhancements | TBD | 🟡 In Progress | Layer relevance-threshold filtering and quality-score ordering ahead of email render. | 2025-10-11 |
| Workflow observability | TBD | 🟡 In Progress | Add Temporal alerting plus Prometheus exporters; document dashboards in `docs/operations.md`. | 2025-10-11 |
| Soft delete support | TBD | ⏳ Pending | Introduce `deleted_at` columns and repository filters per `docs/database-design.md` guidance. | 2025-10-11 |
| Blog fetcher coverage | TBD | ⏳ Pending | Ship non-RSS fetcher path so content pipeline handles blog sources as noted in `docs/processors/content_processing.md`. | 2025-10-11 |
| Quality scorer caching | TBD | ⏳ Pending | Add Redis memoization layer for quality scores to avoid recomputation (`docs/processors/quality_scorer.md`). | 2025-10-11 |
| Summarizer caching | TBD | ⏳ Pending | Implement Redis-backed summary cache for repeated articles per `docs/processors/summarizer.md`. | 2025-10-11 |
| Normalizer rejection metrics | TBD | ⏳ Pending | Emit counters for article rejection reasons flagged in `docs/processors/normalizer.md`. | 2025-10-11 |
| Similarity batching | TBD | ⏳ Pending | Honor `SimilaritySettings.batch_size` to reduce pairwise comparisons (`docs/processors/similarity_detector.md`). | 2025-10-11 |
| Fetcher success metrics | TBD | ⏳ Pending | Add success/failure counters per source as outlined in `docs/processors/fetchers.md`. | 2025-10-11 |
