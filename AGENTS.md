# Repository Guidelines

## Project Structure & Module Organization

Linklet is a React/Vite frontend and FastAPI URL-shortener backend. `frontend/src/` contains pages, components, Axios helpers, and Tailwind styles. In `backend/app/`, routes belong in `api/`, logic in `services/`, database access in `repositories/`, and data types in `schemas/` and `models/`. Tests live in `backend/tests/`; Alembic revisions in `backend/migrations/versions/`. Specifications are in `specs/` and `docs/`.

## Build, Test, and Development Commands

- `docker compose up -d` starts the local PostgreSQL service.
- `cd frontend; npm install; npm run dev` installs frontend dependencies and starts Vite.
- `cd frontend; npm run build` type-checks TypeScript and produces a production build.
- `uv sync --project backend --extra dev` installs the backend and its test/lint tools.
- `uv run --project backend uvicorn backend.app.main:app --reload` starts the API locally.
- `uv run --project backend --extra dev pytest` runs the pytest unit and integration suites.
- `uv run --project backend --extra dev ruff check backend` checks Python style.

Copy `.env.example` to `.env`. Vite runs on port 3000 and proxies `/api` and `/r` to port 8000. `npm run build` type-checks the frontend; no frontend tests or working ESLint setup exists. Never commit secrets or production database URLs.

## Coding Style & Naming Conventions

Use 4-space Python indentation and Ruff's 100-character limit. Use `snake_case` for modules, functions, variables, and tests; `PascalCase` for classes. Keep routes thin; put validation, authorization, and transactions in services/repositories.

Use TypeScript with 2-space indentation. Name React components and page files in `PascalCase` (for example, `CreateLinkModal.tsx`); use `camelCase` for functions, props, and hooks. Prefer existing Tailwind utilities and shared helpers in `frontend/src/lib/`.

## Testing Guidelines

Write pytest tests as `test_<behavior>.py` or `test_<behavior>` in the directory. Cover successful behavior, JWT authorization, invalid URLs, short-code collisions, idempotency, and persistence edge cases. Use in-memory SQLite fixtures in `backend/tests/conftest.py`. Run tests and the frontend build before opening a PR.

## Commit & Pull Request Guidelines

Use Conventional Commit-style messages from history, such as `feat(links): add link deletion` or `chore: update dependencies`. Keep commits focused. Pull requests should explain the change, link related issues/specifications, list validation, and include screenshots for frontend changes. Highlight migrations, environment-variable changes, API-contract changes, and security implications.

## Architecture & Security Notes

Preserve the documented modular-monolith boundaries and database-enforced invariants: unique short codes, link ownership, atomic click counts, and idempotent mutations. Treat client-provided identity as untrusted; enforce authorization server-side. Keep passwords hashed and avoid logging credentials or raw JWTs.
