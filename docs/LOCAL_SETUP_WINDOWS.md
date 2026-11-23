# Windows local setup

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
