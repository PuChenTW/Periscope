# Backend Documentation Map

| Read This | When you're… |
| --- | --- |
| `backend/CLAUDE.md` | spinning up or need the ground rules/tooling reminders. |
| `backend/docs/architecture.md` | mapping service boundaries, dependencies, or data flow for a change. |
| `backend/docs/temporal-workflows.md` | editing/adding workflows or activities in Temporal. |
| `backend/docs/configuration.md` | adding env vars or checking settings defaults/usage. |
| `backend/docs/operations.md` | planning caching/monitoring/security work. |
| `backend/docs/testing-strategy.md` | deciding how/where to add tests or reading coverage expectations. |
| `backend/docs/processors/` | modifying processors in `app/processors/`. |
| `backend/docs/plan_status/status_board.md` | checking active workstreams or historical context. |
| `backend/docs/design-patterns.md` | core design prcinple |

## Quick Navigation

- When touching anything under `app/processors/`, start with the matching doc in `docs/processors/`.
- Workflow changes (Temporal activities/workflows) must cross-check both `temporal-workflows.md` and the processor contract they invoke.
- Configuration additions belong in `configuration.md` **and** note the dependency in the relevant processor doc.
