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
SevaSetu now supports consented requests, verified-worker calendars, coordinator assignment, worker acceptance, outcome review and in-app updates. See [Phase 4 operations](docs/phase4.md), [completion report](docs/phase4-completion.md) and [interview guide](docs/interview-guide.md).

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

SevaSetu's citizen, worker, coordinator and administrator flows are integrated with
five bounded agent workflows. All assignment and completion decisions retain human
review. The local index contains three partial official sources: PM-KISAN, PMSBY
and Telangana Kalyana Lakshmi. Partial evidence never establishes complete eligibility.

English/Hindi/Telugu navigation and notification templates are supported; most forms
and scheme/legal explanations use English fallback. Voice and external SMS/WhatsApp
are not connected. Live LLM inference remains unverified; retrieval-only mode works,
with mocked provider/fallback tests. No government submission, KYC, approval or
MeeSeva affiliation is implied. This is a local development application.

Latest verification: **95 backend tests** against real MongoDB and **20 frontend
tests**, plus TypeScript, lint, production build and four Chrome workflows passed.
See [the completion report](docs/phase4-completion.md) for exact results, source hashes,
remaining risks and the requirement status matrix. Dependency locks describe the
verified local installation; they are not a future security guarantee.

For exact Windows commands, environment variables, endpoint tables, architecture,
agent/lifecycle diagrams, verification policy and production prerequisites, read
[Phase 4 operations](docs/phase4.md). Earlier reports remain historical evidence.
