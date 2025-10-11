# Backend Quickstart (Read Me First)

## Mission

- Keep the backend fast, predictable, and easy for coding agents to extend.
- Ship features that feed the daily digest pipeline; defer everything else.
- Prefer ruthless simplicity over architectural experiments.

## How to Navigate

- Start with @backend/docs/index.md for the full documentation map.
- Processor contracts now live under `backend/docs/processors/`.
- Active workstreams are tracked in `backend/docs/plan_status/status_board.md` with history in `history.md`.

## Toolchain & Execution

- Use `uv run` for every Python command. No bare `python`, no bare `pytest`.

  ```bash
  uv run python main.py
  uv run pytest tests/unit/test_something.py
  ```

- Formatting/linting is managed through `uv run`. Keep commands in scripts/Makefile when possible.
- Temporal worker, Redis, Postgres configs are sourced from environment; see `docs/configuration.md`.

## Core Coding Rules

- **Functional-first**: prefer pure functions + composition. Reach for classes only when the framework forces it (FastAPI models, SQLModel models) or the state really is complex.
- **Return early**: avoid deep nesting; clamp arguments to ≤3 when possible.
- **No Boolean flags** in function signatures. Split functions instead.
- **Docstrings/comments** explain *why*, not *what*. Remove dead code/comments.
- **Text prompts & SQL**: wrap multi-line strings with `textwrap.dedent`.

  ```python
  import textwrap

  SYSTEM_PROMPT = textwrap.dedent("""\
      You are the summarizer.
      Keep output under 500 words.
  """)
  ```

- **Error handling**: raise domain errors, let API layer translate to HTTP. Never swallow exceptions silently.

## When Editing…

- **API layer (`app/api/`)** → confirm request/response schema in `docs/architecture.md`.
- **Services & repositories** → check `docs/design-patterns.md` for repository + DI rules.
- **Temporal workflows/activities** → read `docs/temporal-workflows.md`.
- **Processors** (`app/processors/`) → open the matching file in `docs/processors/`.
- **Settings changes** → update `docs/configuration.md` + any affected processor doc.
- **Testing** → align with `docs/testing-strategy.md`; add fixtures rather than inline mocks.

## Helper Checklist

- New dependency? add to `pyproject.toml`, document the setting, and justify it.
- New processor? follow the standard doc template (purpose, inputs, outputs, failure modes).
- Touching caching, monitoring, security? update the corresponding cheat sheet in `docs/operations.md`.

> **Default stance:** If you can’t explain the change in two sentences, keep trimming until you can.
