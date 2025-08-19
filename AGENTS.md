# Repository Guidelines

## Project Structure & Module Organization
- Root: `todoit-mcp/` (primary package and tooling)
- Core logic: `todoit-mcp/core/` (e.g., `manager.py`, `database.py`, `models.py`)
- Interfaces: `todoit-mcp/interfaces/` (`cli.py`, `mcp_server.py`, `cli_modules/`)
- Tests: `todoit-mcp/tests/` with `unit/`, `integration/`, `edge_cases/`, `e2e/`
- Config: `todoit-mcp/pyproject.toml`, `pytest.ini`, `requirements*.txt`

## Build, Test, and Development Commands
- Setup (editable + dev tools): `pip install -e todoit-mcp[dev]`
- Run CLI locally: `todoit --help` or `python -m todoit-mcp.interfaces.cli --help`
- Tests (all): `pytest -q` (from `todoit-mcp/`)
- Coverage (optional): `pytest --cov=todoit-mcp/core --cov-report=term-missing`
- Format: `black core/ interfaces/ tests/` (run from `todoit-mcp/`)
- Imports: `isort core/ interfaces/ tests/`
- Type check: `mypy core/ --strict`

## Coding Style & Naming Conventions
- Language: Python 3.12+, 4-space indentation, explicit type hints.
- Formatting: `black` (line length 88) and `isort` (profile `black`).
- Types: `mypy` strict in `core/` for public APIs.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `CONSTANT_CASE` for constants, `test_*.py` for tests.

## Testing Guidelines
- Framework: `pytest` (+ `pytest-asyncio` where needed).
- Structure: keep fast unit tests in `tests/unit/`; DB/ORM flows in `tests/integration/`; edge cases in `tests/edge_cases/`; workflows in `tests/e2e/`.
- Fixtures: reuse `tests/conftest.py`; prefer factory helpers over ad‑hoc setup.
- Coverage: add tests for new/changed behavior; prefer functional assertions over implementation details.

## Commit & Pull Request Guidelines
- Commits: Conventional style (e.g., `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`). Keep messages imperative and scoped.
- Branches: `feature/<slug>`, `fix/<slug>`, or `chore/<slug>`.
- PRs: include clear description, linked issues (`Closes #123`), test evidence (output or screenshots for CLI), and notes on migration/compat.
- Pre-merge: run `pytest`, `black`, `isort`, `mypy`; update docs/CHANGELOG when relevant.

## Security & Configuration Tips
- Configuration: CLI reads `.env` when not under pytest. Example: `TODOIT_DB_PATH=/abs/path/to.db`.
- Dev DB: defaults to `~/todoit_dev.db` in dev mode; don't commit local DBs.
- Secrets: never commit real credentials; use `.env.example` as reference.

## Architecture Overview
- Flow: CLI/MCP (`interfaces/`) → `TodoManager` (`core/`) → SQLAlchemy/SQLite.
- Principles: clear separation of concerns, typed core APIs, immutable Pydantic models for IO, and audited history in DB.
