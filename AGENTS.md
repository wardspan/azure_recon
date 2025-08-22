# Repository Guidelines

## Project Structure & Module Organization
- backend/: FastAPI service (Python).
  - main.py (entry), auth.py, exposure.py, identity.py, policy.py, reporting.py, models.py, requirements.txt
- frontend/: React + TypeScript (Vite + Tailwind).
  - src/components/, src/pages/, src/services/, src/contexts/
- templates/: Report templates; reports/: generated outputs
- Docker: docker-compose.yml, Dockerfile.backend, Dockerfile.frontend
- Env/config: .env, init.sql

## Build, Test, and Development Commands
- Run with Docker: `docker-compose up -d` (all services) | `docker-compose logs -f` (tails logs)
- Backend (local):
  - `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
  - `uvicorn main:app --reload --port 8000` (API at http://localhost:8000)
- Frontend (local):
  - `cd frontend && npm install`
  - `npm run dev` (UI at http://localhost:5173)
- Build frontend: `npm run build`; Preview: `npm run preview`

## Coding Style & Naming Conventions
- Python: 4-space indent, PEP 8; snake_case for functions/vars, PascalCase for classes, modules lowercase.
- TypeScript/React: follow ESLint config; PascalCase components, camelCase hooks/vars; keep files under `src/`.
- Files/dirs: descriptive, kebab-case for non-Python assets.
- Formatting: prefer Black/Isort for Python (if installed) and Prettier (optional) for TS; keep imports ordered.

## Testing Guidelines
- No formal test suite in repo yet.
- Backend: add `pytest`-based unit tests near modules (e.g., `backend/tests/test_auth.py`); mock Azure SDK calls.
- Frontend: add React Testing Library + Vitest (or Jest) for components under `frontend/src/__tests__/`.
- Aim for meaningful coverage on auth, scanning orchestration, and report generation.

## Commit & Pull Request Guidelines
- Branches: `feature/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.
- Commits: use Conventional Commits (e.g., `feat: add NSG risk sorting`). Keep messages imperative and scoped.
- PRs: include summary, motivation, screenshots (UI), reproduction steps (bugs), and linked issues. Note breaking changes.
- Checklist: passes lint/build locally; no secrets in diffs; updates docs when behavior changes.

## Security & Configuration Tips
- Secrets: never commit `.env` or credentials. Use device code auth by default; service principal via env vars only when needed.
- Principle of least privilege: requires Reader/Security Reader/Directory Reader roles only.
- Reports may contain sensitive findings—treat `reports/` as confidential artifacts.
