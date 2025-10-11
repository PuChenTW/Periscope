# Processor Common Patterns

## Immutability Contract

All processors follow a pure functional pattern:

- **Input**: Accept `Article` objects and configuration as parameters
- **Output**: Return processor-specific result types (never mutate input articles)
- **Side Effects**: Only caching via injected Redis client; no article mutation

**Rationale**: Immutability enables safe parallel processing in Temporal workflows, clear dependency injection, and predictable testing.

**Example Signatures**:

```python
# Normalizer returns modified Article copy
async def normalize(article: Article) -> Article | None

# QualityScorer returns result object
async def calculate_quality_score(article: Article) -> ContentQualityResult

# RelevanceScorer accepts dependencies as parameters
async def score_article(
    article: Article,
    profile: InterestProfile,
    quality_score: int | None = None,  # Dependency injection
) -> RelevanceResult

# Summarizer accepts topics from TopicExtractor
async def summarize(
    article: Article,
    topics: list[str] | None = None,  # Dependency injection
) -> SummaryResult
```

## Settings Reference

- Processor-specific environment variables live in `backend/docs/configuration.md`.
- In individual processor docs, reference the relevant section instead of duplicating tables.
- When a processor introduces a new setting, update `configuration.md` and add a short note under the processor's **Dependencies** section.

## Shared Failure Modes

| Scenario | Expected Behaviour |
| --- | --- |
| AI provider timeout/error | Processor logs a warning and falls back to the deterministic path (metadata-only score, excerpt summary, skip semantic step, etc.). |
| AI disabled via settings | Processor skips AI calls and relies entirely on deterministic scoring or excerpts while logging at DEBUG. |
| Missing or invalid article fields | Processor returns a neutral/zero score or excerpt, marks the reason in `article.metadata`, and continues pipeline execution. |
| Cache hit | Processor short-circuits work, reusing cached result and logging at DEBUG. |
| Unsupported configuration/style | Processor raises a validation error that the caller converts to a fallback; configuration validation should prevent this in practice. |

Document only **additional** or **processor-specific** failure behaviours in each processor page.
