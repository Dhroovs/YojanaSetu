# Phase 1 verification — 15 November 2026

| Check | Result |
| --- | --- |
| Backend pytest with real MongoDB | 7 passed, 1 warning, 0 skipped (0.63 s) |
| Application import | Passed |
| Ruff lint / format | Passed; 11 Python files formatted |
| pip dependency compatibility | No broken requirements |
| Frontend Vitest | 4 passed across 2 files (692 ms) |
| ESLint | Passed |
| TypeScript and Vite production build | Passed; 23 modules, 430 ms Vite build |
| npm audit | 0 vulnerabilities at verification time |
| Real Chrome + API + MongoDB workflow | Passed; 0 JavaScript page errors |
| Mobile homepage | No horizontal overflow at 390 × 844; screenshot visually inspected |

The browser workflow exercised home navigation, scheme listing, empty search,
education search, details, invalid-token feedback, case creation, tracking, doorstep
intake, Hindi/Telugu availability notices, citizen dashboard and coordinator placeholder.
Temporary ports 5174/8001 and a uniquely named database were cleaned up afterward.
This is smoke testing, not exhaustive accessibility, cross-browser or security testing.

The real-Mongo test covers all six API operations, unique indexes, summary search,
literal regex-like search input, query validation, idempotent seeding, doorstep writes
and case retrieval using a fresh application/Mongo client after an app restart.
Unit tests cover validation, missing records, disabled production access, tokens,
CORS and safe database failures.

## Live checks

- Frontend `http://localhost:5173/`: 200.
- Backend `/docs`, `/openapi.json`, `/api/health`: 200.
- `/api/schemes`, `/api/schemes/demo-learning`: 200; three fictional demo schemes.
- Missing scheme: 404.
- Default case GET/POST and doorstep POST: 403, intentionally disabled.
- Isolated token-enabled case/doorstep POST: 201; case retrieval: 200.
- With MongoDB initially offline, health/discovery returned safe 503 responses.

MongoDB 8.0.16 was downloaded into ignored `.tools/` and started on loopback
127.0.0.1:27017 with data in `.tools/mongodata`. No Windows service was installed.
The main frontend, backend and portable MongoDB were left running. `backend/.env`
enables demo seeding and leaves case access disabled. The database process does not
automatically restart with Windows.

## Fixes

1. Allow both localhost and 127.0.0.1 frontend origins in default/example CORS settings.
2. Compare encoded development tokens to avoid a 500 for non-ASCII configuration.
3. Add regression, Mongo integration, frontend API and repeatable browser checks.

## Repeat integration checks

From `backend/`, with MongoDB running:

```powershell
$env:MONGO_TEST_URI = 'mongodb://127.0.0.1:27017'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
# Node must be on PATH, or set NODE_BINARY to its full executable path.
# Chrome uses its Program Files location, or set CHROME_BINARY.
.\.venv\Scripts\python.exe scripts/verify_browser.py
```

The browser check needs free ports 5174/8001. Tests use and clean up isolated
databases containing only fictional data. Without MONGO_TEST_URI, the Mongo pytest
test is explicitly skipped. Standard frontend/backend commands are in the README.

## Remaining issues and placeholders

- One upstream Starlette/httpx test-client deprecation warning; tests pass.
- Authentication/ownership, worker assignment, actual visits, notifications,
  automated status changes, official submissions and AI implementations are deferred.
- Language selection shows notices; translation is not implemented.
- Citizen dashboard is a navigation hub without personal history. Coordinator is a
  labelled placeholder. Doorstep intake saves records without dispatch or tracking API.
- Fictional schemes only; no verified government ingestion or grounded RAG.
- Catalogue search scans at most 500 records; no indexed search or pagination.
- Shared development token is a local demonstration mechanism, not public authentication.
- Build verified, but no deployment attempted. Phase 2 has not started.
