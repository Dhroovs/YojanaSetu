# Windows setup: fresh checkout and existing demonstration

Use this guide on the development PC. Localhost refers to that PC, not a remote interviewer's machine.
No paid model account is needed for retrieval-only operation. These commands are checked against the
repository's manifests/CLIs; a fresh-machine installation was not repeated during the documentation milestone.

## 1. Software and version checks

Install Git for Windows, Python 3.12, Node 24 LTS, MongoDB Community 8 and Chrome from their official vendors.
Use normal Windows installers and PATH options; do not disable operating-system security if a native wheel
is blocked. Docker Desktop/Compose is optional for a container rehearsal, not a native startup requirement.

```powershell
git --version
py -3.12 --version
node --version
npm --version
mongod --version
```

A Microsoft Store python alias may not be the intended interpreter. The venv's explicit python.exe avoids
that ambiguity. Current project versions are pinned in backend/requirements.lock.txt and frontend/package-lock.json.

## 2. Clone into a new directory and install dependencies

Do not clone on top of an existing checkout or erase its .env/data.

```powershell
git clone https://github.com/Dhroovs/YojanaSetu.git
Set-Location YojanaSetu
py -3.12 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
npm --prefix frontend ci
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
if (-not (Test-Path frontend/.env)) { Copy-Item frontend/.env.example frontend/.env }
```

A virtual environment isolates Python dependencies; npm ci installs the lockfile version set. Copying .env
only when absent preserves existing configuration. Never commit either .env. Install optional browser testing
requirements only if you plan to run the Chrome scripts:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-browser.txt
```

## 3. Configure without inventing secrets

In backend/.env set the intended local URI and these explicit choices; keep unrelated values/private paths:

```dotenv
APP_ENV=development
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DATABASE=yojanasetu
ENABLE_DEMO_DATA=false
ENABLE_DEV_CASE_ACCESS=false
ENABLE_AI=true
EMBEDDING_PROVIDER=onnx
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_PROVIDER=none
ALLOW_HOSTED_LLM=false
ENABLE_CITIZEN_REGISTRATION=true
```

CORS_ORIGINS must include http://localhost:5173 and/or the exact frontend origin used. CHROMA_PATH and
DOCUMENT_STORAGE_PATH default to backend-relative private data directories when starting from backend.
Frontend .env uses VITE_API_BASE_URL=http://localhost:8000/api. VITE values are public build configuration,
never a place for credentials. Settings loads .env relative to the process working directory, so start the
backend/worker/ingestion commands from backend. Do not mix a repo-root data directory with the configured index.

## 4. Start MongoDB first

If installed as a Windows service, inspect Get-Service MongoDB and start it with the appropriate local
operator permissions. Otherwise, in a dedicated PowerShell terminal with mongod on PATH:

```powershell
$demoMongoData=Join-Path $env:LOCALAPPDATA 'YojanaSetu/mongo-data'
New-Item -ItemType Directory -Force $demoMongoData | Out-Null
mongod --dbpath $demoMongoData --bind_ip 127.0.0.1 --port 27017
```

Leave the terminal running. Use a new data directory only for a fresh installation; preserve existing data.
Do not bind an unauthenticated local Mongo service publicly. The portable existing workspace commands are
listed further below; .tools is ignored and is not supplied by cloning the repository.

## 5. Review and ingest the official catalogue

Stop API, worker and any vector writers before ingestion. Read the four manifests and their official sources,
check provenance/currentness and only then pass the operator confirmation flag. No ordinary citizen request
can ingest arbitrary URLs. The first ONNX use may download a local embedding model/cache; it is not a paid API call.

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m app.ai.cli --manifest sources/pm-kisan-portal.json --confirm-reviewed
.\.venv\Scripts\python.exe -m app.ai.cli --manifest sources/pmsby-faq.json --confirm-reviewed
.\.venv\Scripts\python.exe -m app.ai.cli --manifest sources/kalyana-lakshmi-portal.json --confirm-reviewed
.\.venv\Scripts\python.exe -m app.ai.cli --manifest sources/pmsby-rules-pdf.json --confirm-reviewed
```

If an official site changes or TLS fails, stop and review the source. Do not bypass certificate validation,
fabricate text or label a demo as verified. A previously reviewed local PDF/HTML may be supplied through the
CLI's --file/--kind options after its provenance is checked. [Source boundaries](RAG_PIPELINE.md).

## 6. Provision staff and start the platform

From backend, provision only aliases that do not already exist. Passwords are securely prompted, not command-line arguments:

```powershell
.\.venv\Scripts\python.exe -m app.cases.cli --username local-worker --role worker
.\.venv\Scripts\python.exe -m app.cases.cli --username local-coordinator --role coordinator
.\.venv\Scripts\python.exe -m app.cases.cli --username local-admin --role admin
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In another terminal, cd into this checkout's backend and run:

```powershell
.\.venv\Scripts\python.exe -m app.cases.worker
```

In a third terminal, cd into frontend and run:

```powershell
npm run dev
```

Open http://localhost:5173/register or /login. Citizens register themselves; staff do not use a public role
selector. Inspect http://127.0.0.1:8000/docs and /api/ready. A worker needs a submitted profile/availability
and internal admin verification before assignment. [Timed demonstration](DEMO_SCRIPT.md).

## 7. Test, stop and containers

Use [TESTING.md](TESTING.md) for exact checks. Set MONGO_TEST_URI when real-Mongo tests are intended;
otherwise those tests may skip. Do not present skipped integration tests as full verification.
For native servers started in your own terminals, Ctrl+C stops frontend/backend/worker. Stop the Mongo
terminal after writers stop, or use the normal Windows service controls for a managed service. Do not kill
unrelated PIDs or delete a data directory to resolve a port conflict.

If Docker/Compose is installed, the root compose.yaml supports a local rehearsal:

```powershell
docker compose config --quiet
docker compose build
docker compose up -d --wait
# inspect http://localhost:8080/ and /api/ready
docker compose down
```

Do not use down -v against data you want to preserve. A fresh Compose image has no reviewed catalogue or
embedding cache automatically ingested; follow DEPLOYMENT.md/operator review before expecting real RAG.
Remote Linux CI verified synthetic storage/auth/restart behavior, not a full fresh-source production setup.

## Troubleshooting

| Symptom | Check and safe response |
| --- | --- |
| ERR_CONNECTION_REFUSED | Confirm the relevant process exists and health URL responds; a previous session may have stopped its background services |
| Port already in use | Inspect the owning process; reuse the intended instance or stop your own service, not arbitrary processes |
| Mongo503/selection timeout | Mongo process/service, bind/URI, data path and correct database; do not silently replace the user's dataset |
| Missing settings | Correct working directory, preserved backend/.env and explicit opt-in flags |
| Python/wheel failure | Python 3.12 interpreter/venv and platform-compatible pinned wheels; keep OS protections enabled |
| Node/build failure | Node 24, npm ci and lockfile; do not replace versions merely to silence a failure |
| Empty or wrong RAG results | Correct CHROMA_PATH/collection, reviewed active sources, embedding identity and completed ingestion |
| Chroma identity error | Use an explicitly new collection and re-ingest after review; do not mix vector models |
| LLM unavailable | Keep LLM_PROVIDER=none; a configured model name does not establish a running server |
| Login401/429 | Correct alias/password/current role, expiry/reload and real admission window; do not publish credentials or disable guards |
| CORS/network error | Exact frontend origin and API base URL; localhost/127.0.0.1 are different origins |
| Reminder not visible yet | Worker running, persisted due time, quiet/frequency preferences and latest record revision |
| Proxy502 after restart | Use the checked-in Docker DNS-aware Nginx config and readiness checks; inspect actual health rather than assuming container running means ready |

## Existing prepared Windows workspace

The notes below describe the already configured E:\YojanaSetu\YojanaSetu machine and its cached Node/portable
Mongo tools. They are not a requirement for other developers. The inspection environment has separate
synthetic data and Windows-encrypted role access. Preserve it if already running.


## Running inspection environment

The final mission maintains an isolated synthetic demo on ports5173/8000; check its
health before starting competing services. LOCAL_DEMO_ACCESS.md provides secure local
role access/restart commands. Existing normal .env and citizen datasets are preserved.

Verified workspace: `E:\YojanaSetu\YojanaSetu`, Python 3.12 virtual environment and
cached Node runtime. For a fresh checkout install Python 3.12, Node 24, MongoDB 8 and
Chrome; then create the venv, install the lockfile and run `npm ci`. Browser tests also
need `backend/requirements-browser.txt`. Native wheels can be restricted by Windows
application control; do not disable OS security to install an incompatible wheel.

From the repository root, start the existing portable Mongo if port 27017 is free:

```powershell
$mongoBinary=(Get-ChildItem .tools/mongodb -Recurse -Filter mongod.exe | Select-Object -First 1).FullName
Start-Process -FilePath $mongoBinary -ArgumentList '--dbpath','E:\YojanaSetu\YojanaSetu\.tools\mongodata','--bind_ip','127.0.0.1','--port','27017','--logpath','E:\YojanaSetu\YojanaSetu\.tools\mongodb.log','--logappend' -WindowStyle Hidden
Set-Location backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
```

Preserve existing `.env`. Core settings: `MONGODB_URI=mongodb://127.0.0.1:27017`,
`MONGODB_DATABASE=yojanasetu`, explicit `CORS_ORIGINS`, private `DOCUMENT_STORAGE_PATH`,
`CHROMA_PATH`, `ENABLE_AI=true`, ONNX embeddings, `LLM_PROVIDER=none`, and
`ALLOW_HOSTED_LLM=false`. Registration can be disabled with
`ENABLE_CITIZEN_REGISTRATION=false`. The complete defaults/limits are in `.env.example`.
Do not expose the development instance publicly; see the dependency blocker in SECURITY.md.

Provision staff once, with securely prompted passwords, then start the backend:

```powershell
.\.venv\Scripts\python.exe -m app.cases.cli --username local-worker --role worker
.\.venv\Scripts\python.exe -m app.cases.cli --username local-coordinator --role coordinator
.\.venv\Scripts\python.exe -m app.cases.cli --username local-admin --role admin
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Citizens can register through `/register`; staff accounts are never public signup roles.
Do not reprovision an existing alias. In a second backend terminal run the scheduler:

```powershell
Set-Location E:\YojanaSetu\YojanaSetu\backend
.\.venv\Scripts\python.exe -m app.cases.worker --purge-expired
```

In a third terminal:

```powershell
Set-Location E:\YojanaSetu\YojanaSetu\frontend
$env:PATH='C:\Users\dhroo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
node ..\.tools\package\bin\npm-cli.js run dev
```

Open `http://localhost:5173/register` or `/login`. Health is `/api/health`, liveness
`/api/live`, and database/index/private-directory readiness `/api/ready` on port 8000.
Refreshing clears the tab's bearer session; sign in again. Navigation language persists
on the device; the account page can save a language for future sign-ins.

For a fresh catalogue, review and ingest the four manifests using `python -m app.ai.cli
--manifest sources/<name>.json --confirm-reviewed` with writers stopped. Native local
embeddings may need an initial model download/cache; no model API credit is required.
Authenticated Scheme Matcher needs no development secret. Anonymous legacy demo routes
remain explicitly development-only and require the configured development token.

Fresh dependencies: `python -m venv backend/.venv`, install the backend lock, then in
frontend `npm ci`. On ordinary Node installations use `npm` instead of the cached
`node ..\.tools\package\bin\npm-cli.js` wrapper. See TESTING.md and DEMO_SCRIPT.md.
