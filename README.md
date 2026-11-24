# YojanaSetu + SevaSetu - Phase 5 local release candidate

An integrated welfare-information and citizen-assistance application using React,
TypeScript, FastAPI, MongoDB, LangGraph, local ONNX embeddings and Chroma retrieval.
Five bounded agent workflows connect source-backed scheme guidance, private document
assistance, durable follow-ups/escalation and consented doorstep visits.

**Public backend release is blocked by unresolved upstream ChromaDB advisories.** The application
uses an embedded local client and does not expose Chroma HTTP endpoints, but no patched
package version was available at verification. Remote Linux CI verified container
startup, restart/replacement and persistence. Live LLM and native speech remain
unverified. This is not production certification, government authorization, an official
MeeSeva partner or a publicly deployed backend.
No paid API call or cloud resource was used. See docs/FINAL_RELEASE_REPORT.md for actual
GitHub/public-showcase results; no complete public backend is claimed.

## Published interview showcase

**https://dhroovs.github.io/YojanaSetu/** is a verified free static showcase with
16 real synthetic workflow screenshots. It is not a publicly hosted backend.
The complete code is pushed to this repository's main branch. See
[the release report](docs/FINAL_RELEASE_REPORT.md) for CI results and remaining gates.

## Run locally

The isolated synthetic inspection app runs at **http://localhost:5173/**, with API
 docs at **http://127.0.0.1:8000/docs** while services remain running.
[Demo role access](docs/LOCAL_DEMO_ACCESS.md) explains locally encrypted temporary
passwords. [Final release report](docs/FINAL_RELEASE_REPORT.md) records **108 backend
and 25 frontend tests**, five browser regressions and16 inspection screenshots.
[Strictly free hosting review](docs/FREE_HOSTING_REVIEW.md) explains hosting limits.


Exact Windows startup/provisioning: [LOCAL_SETUP_WINDOWS.md](docs/LOCAL_SETUP_WINDOWS.md).
Start MongoDB, backend and the durable worker, then the frontend. Open
http://localhost:5173/register or /login. Citizens can register; staff roles require
operator/admin approval. Authenticated matching needs no shared development secret.

From backend, after reviewing `.env.example` and preserving any existing `.env`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
# Separate terminal, same directory:
.\.venv\Scripts\python.exe -m app.cases.worker --purge-expired
```

From frontend, using a normal Node 24 installation:

```powershell
npm ci
npm run dev
```

The current machine's cached Node/npm commands are documented in the Windows guide.
Use synthetic data during development. Sessions stay in tab memory and are cleared
on reload/logout. Language can persist on the device and be saved to the account.

## Working scope and evidence

- Public scheme discovery and source coverage; three schemes/four partial official
  documents, including an actual government rules PDF with page-level citations.
- Individual signup/login, role and object authorization, private PDF/image assistance,
  human checklist review, case activity and durable localized notices/reminders.
- Five controlled agents with deterministic rules, grounded responses, safe retries,
  explicit human gates and session-owned conversations/results.
- SevaSetu request, review, verified-worker eligibility, atomic calendar conflicts,
  assignment proposal/acceptance, check-in, outcome review, feedback and follow-up.
- Administrator user/role operations, verification, organizations and sanitized status.
- English/Hindi/Telugu draft static dictionaries with measured coverage, language
  persistence and source-language fallback. Speech consent/controls/text fallback are
  tested; native transcription/playback is not certified for any language.
- Local ONNX/retrieval-only mode works. Hosted models and external messaging remain
  disabled/unconfigured. Optional provider protocols have mock tests, not live delivery.

Read [FINAL_HANDOFF.md](docs/FINAL_HANDOFF.md) for exact executed pass/fail/skip counts,
release gates, source and language evidence, Docker/CI status and continuation steps.
The Python advisory gate intentionally fails until the unresolved dependency issue is
resolved or independently reviewed and explicitly approved. Passing unit tests do not
mean the security/deployment gates passed.

## Documentation

- [Architecture](docs/ARCHITECTURE.md), [agents](docs/AGENTS.md), [RAG](docs/RAG_PIPELINE.md)
- [SevaSetu workflow](docs/SEVASETU_WORKFLOW.md), [API](docs/API_REFERENCE.md), [database/recovery](docs/DATABASE.md)
- [Security](docs/SECURITY.md), [known limitations](docs/KNOWN_LIMITATIONS.md), [deployment](docs/DEPLOYMENT.md)
- [Testing](docs/TESTING.md), [completion matrix](docs/PHASE5_COMPLETION_MATRIX.md)
- [Interview guide](docs/INTERVIEW_GUIDE.md), [demo script](docs/DEMO_SCRIPT.md)

No Phase 6 has been started. Historical phase reports remain evidence of earlier
checkpoints; current canonical documents above take precedence for project status.
