# Repository Guidelines

## Project Structure & Module Organization
- Core modules live at the repo root: `main.py` (CLI), `server.py` (FastAPI web server), `github_client.py` (GitHub API wrapper), `commit_agent.py` (cache + AI summaries), `board.py` (scoring and ranking).
- Config/data files are also at the root: `models.json` (LLM endpoints/keys) and `cache.json` (cached repo data).
- Test utilities are `test_*.py` scripts (async, run directly).
- Packaging metadata is in `pyproject.toml` and `uv.lock`.

## Build, Test, and Development Commands
- `uv sync` installs Python dependencies for the project.
- `uv run python main.py` runs the CLI dashboard.
- `uv run python server.py` starts the web dashboard at `http://localhost:8000`.
- `uv run python test_time_travel.py` (or other `test_*.py`) runs ad-hoc verification scripts.

## Coding Style & Naming Conventions
- Use Python 3.12 with 4-space indentation and PEP 8 spacing.
- Naming: `snake_case` for functions/variables, `CamelCase` for classes, and lowercase module names.
- Keep async boundaries explicit (`async def` for I/O), and keep functions small and readable.
- JSON config keys follow `snake_case` (see `models.json.example`).

## Testing Guidelines
- There is no formal test runner; tests are direct scripts in `test_*.py`.
- These scripts hit live GitHub endpoints, so ensure `GITHUB_TOKEN` is set and watch rate limits.
- Add new tests as focused scripts or extend existing ones with clear console output.

## Commit & Pull Request Guidelines
- Recent commits use short, imperative messages (e.g., “Fix timezone comparison bug in cache refresh logic”).
- Keep commits narrowly scoped; include rationale in the body if the change is subtle.
- PRs should include a summary, testing notes, and screenshots for UI changes.

## Configuration & Secrets
- Set `GITHUB_TOKEN` in your environment for GitHub API access.
- Store AI provider credentials in `models.json` (copy from `models.json.example`); do not commit real secrets.
