# Tests and reproducible evidence

## Subsequent final verification

FINAL_RELEASE_REPORT.md records108 backend and25 frontend passing tests and fresh
browser evidence. scripts.verify_inspection_demo checks the running synthetic demo,
actual scheduler delivery, private access denial and a synthetic admin review-note
mutation. It produces 16 screenshots. It needs local Windows DPAPI access and is not
a CI unit test. Never run scripts.local_demo access in captured CI/tool logs.

Use synthetic data only. The backend suites use isolated test databases; real MongoDB
is enabled by `MONGO_TEST_URI`. Without it Mongo-specific tests are skipped, so always
report pass/fail/skip counts. Unit providers use mock transports and never paid APIs.

From the repository root:

```powershell
$env:MONGO_TEST_URI='mongodb://127.0.0.1:27017'
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
.\backend\.venv\Scripts\python.exe -m ruff check backend/app backend/tests backend/scripts
.\backend\.venv\Scripts\python.exe -m ruff format --check backend/app backend/tests backend/scripts
.\backend\.venv\Scripts\python.exe -m pip check
Set-Location frontend
$env:PATH='C:\Users\dhroo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
node ..\.tools\package\bin\npm-cli.js test
node ..\.tools\package\bin\npm-cli.js run lint
node ..\.tools\package\bin\npm-cli.js run build
node scripts/localization-report.mjs
node ..\.tools\package\bin\npm-cli.js audit --audit-level=high
```

With Chrome, Node and the browser requirements installed, from backend:

```powershell
$env:NODE_BINARY='C:\Users\dhroo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
.\.venv\Scripts\python.exe -m scripts.verify_browser
.\.venv\Scripts\python.exe -m scripts.verify_phase2_browser
.\.venv\Scripts\python.exe -m scripts.verify_phase3_browser
.\.venv\Scripts\python.exe -m scripts.verify_phase4_browser
.\.venv\Scripts\python.exe -m scripts.verify_phase5_browser
.\.venv\Scripts\python.exe -m scripts.verify_phase4_sources
.\.venv\Scripts\python.exe -m scripts.verify_phase2
.\.venv\Scripts\python.exe -m scripts.dependency_audit --report ../artifacts/python-security-audit.json
```

The advisory command exits nonzero when findings remain; this is expected for current
ChromaDB, not a successful security check. Browser scripts start/stop temporary loopback
servers and disposable databases. Phase 2/5 integration needs the reviewed live local
source/vector index; ordinary unit tests do not. The Phase 5 test exercises individual
login against `APP_ENV=production` without any development secret, actual PDF checklist
upload, multilingual forms/persistence, five agents on linked context and voice fallback.

Final executed results and exact counts are in FINAL_HANDOFF.md. Browser results are
not formal WCAG certification. Mocked speech exercises consent/controls/fallback,
not live microphone transcription. Model protocol/usage tests do not verify live LLM
inference. Backup tests check synthetic Mongo/index/file fixtures, not production
disaster recovery. Final remote CI verified Linux container startup/proxy/auth and persistence across
restart/replacement; overall CI still fails the dependency gate. See FINAL_RELEASE_REPORT.md.

Container CI executes scripts/verify_container_runtime.py against disposable Compose
services; no physical/official visit is implied. It checks a separate synthetic vector
collection, not downloaded source embeddings or a production disaster-recovery drill.
