# Processor Doc Template

Use this structure for every processor-specific document.

## Purpose

- Single sentence explaining what the processor does and why it exists.

## Inputs

- Bullet list of required fields on `Article`/other objects before this processor runs.

## Outputs

- What fields are mutated or produced (e.g., `article.metadata["quality_score"]`).

## Dependencies

- Settings object(s) — reference `backend/docs/configuration.md` instead of duplicating tables.
- External services (AI provider, Redis, etc.)

## Hot Path / Algorithm

- Ordered list or short paragraph describing the main steps.

## Failure Modes

- Link to shared behaviours in `common_patterns.md`.
- Only document deviations or processor-specific responses.

## Metrics & Instrumentation

- Which metrics/logs this processor emits (if any) and where to configure them.

## Settings

- Note which settings group(s) apply and point to the relevant section in `backend/docs/configuration.md`.

## Tests

- Point to files under `tests/` that cover this processor.

## Changelog

- Date-ordered bullets capturing feature-complete milestones or major tweaks.

Keep each section terse. If you feel the urge to paste code, link to the module instead.
