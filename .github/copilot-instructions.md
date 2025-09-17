# Project-specific instructions for AI coding agents

This file captures the minimal, actionable knowledge an AI agent needs to be productive in the Tears 2025 backend.

Keep this short and specific — prefer examples and file references over generic advice.

1. Big picture
- FastAPI backend (entry: `app/main.py`) providing API endpoints and a small set of internal routes under `/internal`.
- SQLAlchemy ORM models under `app/models/*` with Alembic migrations in `alembic/versions/`. Tests run against a local SQLite `dev.db` by default.
- Services live in `app/services/*`: HTTP client (`espn_client.py`), transformer (`transformer.py`), and orchestration (`sync.py`). The orchestration flow is: `routes -> espn_client.fetch_games_for_week -> transformer.transform_espn_response -> sync.transform_and_sync_games`.

2. Key files to read first
- `app/main.py` — app composition and router registration.
- `app/db.py` — lazy engine/session factory. Tests often change `DATABASE_URL` at runtime; this module recreates engine/session when env changes.
- `app/core/config.py` — pydantic settings (reads `.env`). `INTERNAL_SYNC_TOKEN` may be set here.
- `app/routes/internal_sync.py` — internal POST endpoint that triggers the ESPN sync (protected by `X-Internal-Sync-Token`).
- `app/services/espn_client.py`, `app/services/transformer.py`, `app/services/sync.py` — fetch, normalize, and persist pipeline.
- `alembic/env.py` — alembic imports `app.models` for autogeneration; changing model locations requires updating this file.

Note: this repo uses Taskmaster for task-driven workflows. See `.github/instructions/dev_workflow.instructions.md` and `.github/instructions/taskmaster.instructions.md` for the AI agent workflow and available MCP/CLI tools.

3. Important patterns & conventions
- Lazy DB engine: `app/db.py` uses an engine proxy and recreates engine/session when `DATABASE_URL` changes. Tests rely on this to point to in-memory or file-based SQLite instances.
- Transaction handling: `transform_and_sync_games` uses nested transactions if `db.in_transaction()` is True (use `db.begin_nested()` to be safe when called within existing transactions).
- Transformer: defensive parsing in `app/services/transformer.py` — skips malformed events and maps ESPN-specific abbreviations/statuses (e.g., `JAC -> JAX`, `WSH -> WAS`, `inprogress -> in_progress`). Follow these mappings when integrating new data.
- Tests add the project root to `sys.path` in some modules (see `tests/test_health.py`) — follow the same import strategy to keep tests robust.

Agent-specific workflow notes (from dev_workflow.instructions.md):
- Default stance: operate in the `master` task context unless the user requests otherwise.
- Basic loop to follow when managing work with Taskmaster: `list` → `next` → `show <id>` → `expand <id>` → implement → `update-subtask` → `set-status`.
- Introduce tagged task lists only when needed (branches, experiments, team collaboration). Use `task-master add-tag --from-branch` or the MCP equivalent.

4. Developer workflows (commands)
- Dev server: `uvicorn app.main:app --reload` or `poetry run start` (defined in `pyproject.toml`).
- Tests: `pytest -q` (project uses `pytest` + `httpx` for ASGI tests).
- Migrations:
  - Set `DATABASE_URL` in `.env` or env var.
  - `python -m alembic revision --autogenerate -m "message"`
  - `python -m alembic upgrade head`
- Running specific tests (fast iteration): `pytest tests/test_internal_sync.py -q` or target files directly.

Taskmaster tips:
- Prefer MCP tools when available (`get_tasks`, `next_task`, `get_task`, `expand_task`, `update_subtask`, `set_task_status`). The MCP server provides structured responses and avoids CLI parsing issues.
- For quick actions in a terminal, the `task-master` CLI mirrors MCP commands. Use `task-master next` to fetch the next actionable item.

5. Integration points & runtime expectations
- ESPN API base URL can be overridden with `ESPN_BASE_URL` env var for local testing. `app/services/espn_client.py` accepts an optional `session` param for injecting mocks.
- Internal sync endpoint requires header `X-Internal-Sync-Token` matching `settings.INTERNAL_SYNC_TOKEN`.
- Alembic autogeneration expects models to be importable via `app.models.*` as referenced in `alembic/env.py`.

6. Tests and edge cases the AI should respect
- SQLite datetime: code converts ISO strings to `datetime` objects before inserting (see `sync.py`). Ensure any new inserts follow same approach.
- Duplicate Week rows: `transform_and_sync_games` chooses latest `Week` by `id` when multiple matches exist — maintain this defensive behavior.
- External deps may be missing in test environments (e.g., `requests`); `espn_client` uses lazy imports and tests may `pytest.importorskip("requests")`.

Rule & self-improvement guidance (from self_improve.instructions.md and vscode_rules.instructions.md):
- When you see repeated patterns across 3+ files or recurring review comments, propose adding/updating a rule in `.github/instructions/`.
- Rules should be actionable, include concrete examples from the codebase, and reference the file(s) that motivated them.
- After significant refactors, update instruction docs so future agents follow new patterns.

7. Example snippets (how to call, mock, or extend)
- To call the internal sync endpoint in tests:
  - Set `settings.INTERNAL_SYNC_TOKEN = "token"`
  - Use `TestClient(app).post("/internal/sync-games/espn?year=2025&week=1", headers={"X-Internal-Sync-Token": "token"})`
- To mock the ESPN client in tests: patch `app.routes.internal_sync.fetch_games_for_week` or call `fetch_games_for_week(..., session=mock_session)`.

8. When changing DB models
- Update `alembic/env.py` imports if models move. Use `Base.metadata.create_all(bind=engine)` in tests where needed.
- Ensure the migrations' `down_revision` chain remains valid before committing migration files in `alembic/versions/`.

9. Files you will likely edit when adding features
- `app/routes/*.py` — routes and endpoint wiring
- `app/services/*.py` — new business logic and transformations
- `app/models/*.py` — ORM model changes (also update Alembic migrations)
- `app/db.py` — only if you need custom engine behavior; prefer reusing proxy pattern

10. Ask for missing context
- If a change requires environment secrets (e.g., production token, DB URL), ask for explicit values rather than inventing defaults.

If you want me to expand this into a short PR checklist (CI tests to run, files to update, migration steps), say the word and I'll add it.

If anything here is unclear or you'd like me to expand a section (example tests, migration steps, or developer checklist), tell me which part and I'll iterate quickly.