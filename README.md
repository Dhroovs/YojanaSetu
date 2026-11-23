# YojanaSetu + SevaSetu — Phase 3

A runnable local development foundation for scheme discovery, assistance cases and
doorstep request intake, extended with a LangGraph scheme matcher and source-grounded
Chroma retrieval. Fictional demos are labelled separately from reviewed official sources.
This is not a government service. Use fictional citizen profiles during development.
No paid provider is enabled by default.

## Phase 3 private assistance

Individual login, Citizen/Worker/Coordinator/Admin permissions, private document
uploads, human checklist review, durable in-app follow-ups, escalations and a bounded
multi-agent case assistant are implemented. Read [Phase 3 setup and security notes](docs/phase3.md).
Never use real citizen documents in this development preview. Internal completion
does not mean official government approval or KYC.

With MongoDB running, from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m app.cases.cli --username local-citizen --role citizen
.\.venv\Scripts\python.exe -m app.cases.cli --username local-coordinator --role coordinator
# Passwords are prompted securely. Provision worker/admin accounts similarly when needed.
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run `.\.venv\Scripts\python.exe -m app.cases.worker --purge-expired` in another backend
terminal, then start the frontend as below. Open http://localhost:5173/login.
Pending reminders survive restarts because schedules are in MongoDB; the worker must
be running for delivery and physical retention cleanup. Refreshing the browser clears
the memory-only sign-in session. There is no public registration or role selection.
Phase 4 Doorstep Coordinator remains unimplemented.

## Phase 2 quick start

Complete the Windows setup below, start MongoDB, then configure `backend/.env`:

```dotenv
APP_ENV=development
ENABLE_AI=true
ENABLE_DEV_CASE_ACCESS=true
DEV_ACCESS_TOKEN=your-own-random-token-of-at-least-32-characters
EMBEDDING_PROVIDER=onnx
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_PROVIDER=none
```

`none` is real semantic retrieval plus deterministic checks and extractive citations,
**without an LLM**. The first embedding operation downloads about 80 MB of model data.
For a local LLM, install Ollama, run `ollama pull qwen2.5:3b`, then set
`LLM_PROVIDER=ollama` and `LLM_MODEL=qwen2.5:3b`. No LLM is installed or tested here;
its adapters have mocked protocol tests. See model costs, hardware and limitations
in [Phase 2 documentation](docs/phase2.md).

Review a source before indexing. From `backend/`, with MongoDB running:

```powershell
.\.venv\Scripts\python.exe -m app.ai.cli --manifest sources/pm-kisan-portal.json --confirm-reviewed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run the frontend as below, open http://localhost:5173/assistant and enter the local
development token. The reviewed PM-KISAN page is partial and dated; the assistant
warns about this and withholds a positive eligibility conclusion. A manifest is
included, but MongoDB/Chroma contents are local data, not committed artifacts.

## Structure

- `frontend/`: React, TypeScript, Vite, Tailwind and React Router.
- `backend/app/`: FastAPI, Pydantic models, async MongoDB repository, demo ingestion.
- `backend/app/agents/`: Scheme Matcher, three case-assistance agents and bounded orchestration;
  Doorstep Coordinator remains deferred.
- `backend/app/cases/` and `auth.py`: private case lifecycle, authorization, storage,
  provisioning, scheduling, review and escalation APIs.
- `backend/app/ai/`: source ingestion, Chroma, model adapters, rule/citation models,
  protected API and Mongo conversation memory.
- `backend/tests/`: API workflow, validation, access restriction and failure tests.
- `docs/architecture.md`: module boundaries, security decisions and deferred work.

## Windows PowerShell setup

Install Python 3.12 (with pip), Node.js 22.12+ LTS, and MongoDB Community locally.
Ensure Python, Node and npm are on PATH. Start the local MongoDB service using
its installer/service configuration. Use a separate development database.

From the repository root, prepare the backend:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

The copied configuration enables fictional scheme seeding. Case services stay
disabled. To try case and doorstep flows locally, edit `backend/.env`:

```dotenv
ENABLE_DEV_CASE_ACCESS=true
DEV_ACCESS_TOKEN=replace-with-your-own-random-token-at-least-32-characters
```

Generate a token if desired:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the same token into the relevant local form. Do not put it in frontend env
variables or commit it. Run the backend from `backend/` so `.env` is loaded:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal, from the repository root:

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.
If Vite chooses another port, update backend `CORS_ORIGINS` and restart it.
For localhost MongoDB without authentication, retain loopback binding and use
fictional data only. Supply all connection settings through environment variables.

## Verification commands

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

From `frontend/`:

```powershell
npm run test
npm run lint
npm run build
```

Unit tests use an injected test repository and need no running MongoDB. Real MongoDB
persistence and Chrome workflow checks have also passed. See
`docs/phase1-verification.md` for exact results and repeatable integration commands.

## Scope and limitations

Implemented flows: API-backed scheme search/details, local case creation and lookup,
doorstep request storage, semantic scheme matching, cited rules, follow-up memory,
responsive navigation, loading/error/empty states, authenticated owned cases, private
document reviews, durable reminders and internal human referral. Worker dispatch and
translation are not connected. Local LLM use is optional.
No real eligibility decision, KYC or official submission occurs. Case access is
restricted to explicitly enabled local development. See architecture notes before
extending security or ingestion. Phase 4 has not started.

Verification uses bundled runtimes because Python and Node/npm were absent from PATH.
Backend: 72 pytest tests passed with real MongoDB; imports, Ruff lint and format passed.
`requirements.lock.txt` records the installed backend versions (Python 3.12, Windows).
Frontend: 12 tests passed; ESLint and the TypeScript/Vite
production build passed. Dependency audit reported zero vulnerabilities after
upgrading tools and the router. A scoped minimatch override patches a transitive
lint dependency; revisit it when typescript-eslint updates its dependency range.
`frontend/package-lock.json` records the verified dependency tree. These audit
results describe the installation at verification time, not a future guarantee.

RAG details: [docs/phase2.md](docs/phase2.md). Current case-assistance run commands,
API reference, security limitations and workflow diagrams: [docs/phase3.md](docs/phase3.md).

Suggested commit: `feat: add authenticated multi-agent case assistance and durable follow-ups`
