# Final demonstration and release report

Local verification: 23 November 2026; final push/publication closure: 24 November 2026.
Baseline: `f631208`.
Repository confirmed by owner: https://github.com/Dhroovs/YojanaSetu, branch `main`,
existing public visibility unchanged. Repository API confirms push permission; no
unrelated remote branches/commits were present during preparation.

**Overall: Verified Working locally; complete public backend deployment is Blocked
by External Dependency.** No complete live application URL is claimed. The separate static interview showcase
is **Verified Working** at https://dhroovs.github.io/YojanaSetu/ . No paid plan,
credit card, trial, paid model, SMS/WhatsApp send or billable resource was used.

## Actual local application

- Frontend: **http://localhost:5173/**
- FastAPI docs: **http://127.0.0.1:8000/docs**
- Health and readiness: `http://127.0.0.1:8000/api/health`, `/api/ready`, HTTP **200**.
- Frontend homepage: HTTP **200**. MongoDB runs on loopback port 27017.
- Background scheduler: active against the dedicated synthetic demo database.
- Chroma: embedded persistent index; no separate HTTP Chroma service is required.
- Account passwords: locally encrypted, never included in this report or Git.
  [Safe access commands and roles](LOCAL_DEMO_ACCESS.md).

## Exact final local checks

| Check | Status | Actual result |
| --- | --- | --- |
| Complete backend pytest with real Mongo | Verified Working | **108 passed, 0 failed, 0 skipped in 155.43 seconds** |
| Frontend Vitest | Verified Working | **25 passed, 9 files, 0 failed, 0 skipped in 1.85 seconds** |
| Frontend ESLint | Verified Working | Exit 0 |
| TypeScript + production Vite build | Verified Working | Exit 0; 33 modules, final Vite 890ms |
| Ruff lint/format | Verified Working | All checks passed; 70 files formatted |
| Python package consistency | Verified Working | No broken requirements found |
| npm audit | Verified Working | 0 vulnerabilities; 334 dependencies reported |
| Python OSV audit | Blocked by External Dependency | Exit 1; chromadb 1.5.9 has four GHSA findings plus four PYSEC aliases; 119 packages scanned |
| Existing browser suites | Verified Working | All five scripts passed, zero JS page errors |
| Real-source integration | Verified Working | PMSBY/Kalyana Lakshmi retrieval and citations; coverage 3 schemes / 4 sources; no LLM called |
| Persistent demo browser inspection | Verified Working | **16 screenshots**, real RAG/reminder/admin mutation and auth isolation; zero JS errors |
| Simulated completed-visit fixture | Verified Working | Real API acceptance/en-route/check-in/outcome/human review/feedback persisted; explicitly no real service |
| Local Docker/Compose runtime | Not Tested | Docker not installed at normal path or on PATH; YAML parsed previously |
| Live Ollama/hosted LLM | Not Tested | Local `/api/tags` connection failed; hosted calls remain disabled |
| Native microphone/playback | Not Tested | Mocked consent/controls and real unsupported-browser fallback only |

The earlier 107-test run passed in 149.60s before the new demo-only account regression
was added. The final 108 count supersedes it. Browser suites are
`verify_browser`, `verify_phase2_browser`, `verify_phase3_browser`,
`verify_phase4_browser`, and `verify_phase5_browser`. The first script also checks
historical anonymous development paths and its legacy coordinator placeholder; it
does not establish the private coordinator's functionality. The later role-based
scripts and persistent demonstration verify the real private coordinator screens.

New inspection assertions cover login/logout across citizen/coordinator/worker/admin,
real reviewed RAG, private PDF persistence, actual background reminder delivery,
persisted referral, citizen denial from admin API, worker denial from unassigned
private case, safe operations and a real synthetic admin account review-note update.
[Inspection screenshots](demo-evidence/03-citizen-dashboard.png) include no passwords,
tokens, contact details or real citizen data.

## Functional status by capability and role

| Capability | Status | Evidence / boundary |
| --- | --- | --- |
| Scheme Matcher | Verified Working | Real local ONNX retrieval, citations, source freshness/unknown eligibility and follow-up memory; deterministic evidence-only mode |
| Document Verifier | Verified Working | Real source checklist/PDF upload, type/size/readability checks and human checklist review. No legal authenticity certification |
| Follow-up Agent | Verified Working | Durable jobs, scheduled reminders, quiet hours, duplication controls and acknowledgement; actual running demo delivery observed |
| Escalation Agent | Verified Working | Human-assistance referral, coordinator claim/acknowledgement/resolution and audit via graph/API/browser tests |
| Doorstep Coordinator | Verified Working | Eligible verified-worker ranking, consent/availability, confirmed assignment, current state and bounded guidance; no autonomous final approval |
| Citizen journey | Verified Working | Signup/login, discovery/details, RAG/citations, private case/PDF, timeline, reminder/referral, booking/tracking, language/fallback and reviewed feedback |
| Worker journey | Verified Working | Profile/calendar, assigned visits, acceptance, en-route/check-in/outcome, protected citizen details; future assigned demo record retained |
| Coordinator journey | Verified Working | Owned queues, document/referral management, eligibility review, claim/approve/assign and human outcome completion; conflict checks tested with real Mongo |
| Administrator journey | Partially Working | Real users/roles/operations and worker verification/organizations/service areas; source writes remain reviewed operator CLI, account audit is persisted rather than a separate audit UI |
| Mongo and Chroma RAG | Verified Working | Real Mongo persistence/isolation and copied public local vector index; Chroma security gate remains separately blocked |
| English/Hindi/Telugu | Partially Working | en UI and draft hi/te static coverage456/456 captured phrases,534 entries; major browser paths/persistence pass. Native review and free-text multilingual RAG not certified |
| Voice | Partially Working | Consent, editable transcript, stop/replay controls and fallback tested; en-IN/hi-IN/te-IN selected, physical speech not established in any language |
| In-app notifications | Verified Working | Case/visit events, language preferences, durable outbox, replay/quiet-hour/frequency and acknowledgement tests |
| WhatsApp/SMS | Blocked by External Dependency | Adapters mocked, credentials/templates/callbacks/live sending unconfigured. No paid calls or messages |
| Real local/hosted model inference | Not Tested | No successful real model call; mock protocol/usage/fallback tests are not live inference |
| Complete public hosted platform | Blocked by External Dependency | No reviewed no-card INR 0 host meets current worker/persistence needs; Chroma advisory also blocks public backend release |

Three agent capabilities are deterministic case-graph nodes, not five independent
model conversations. Actor-authorized shared case context and explicit human gates
are maintained. Durable state is domain records/receipts/jobs, not raw prompt history.
NGO volunteer is a worker profile kind supported by the worker role, not a new auth role.

Government coverage: PM-KISAN, PMSBY and Kalyana Lakshmi, four reviewed partial
official sources including the actual PMSBY Rules PDF. Sources retain hash/version,
publisher/URL/review evidence and page citations. PMSBY's two sources need human
reconciliation; no missing official fact was invented. See SOURCE_COVERAGE.json.

## Fixes, security and privacy

New demo accounts have `demo_only=true`; login and existing bearer-session checks
reject them outside development. A real-Mongo regression verifies both rejection
paths while leaving ordinary accounts usable. The helper binds backend/frontend to
loopback, uses separate Mongo/files/vectors and Windows DPAPI for temporary passwords.
The scheduler starts after fixture seeding to avoid CAS races. Explicit ranking
override reasons are retained when selecting a non-top worker for a demonstration.
No production authorization or rate limit was bypassed to make the demo pass.

Existing checks cover role/object authorization, worker assignment isolation,
session expiration/revocation/logout, citizen-only registration, scrypt/password
whitespace, file validation/access, concurrent reservations, idempotency, privacy-safe
logs and hostile/unsupported source/model output. No intrusive external testing occurred.

History secret scan:222 text blobs inspected for high-confidence key/private-key/
credentialed-URL patterns. The only candidate was the deliberate rejected test URL
`https://user:pass@x.gov.in/a` in `test_phase2.py`; it is not an active credential.
Current added source/configuration/screenshots were inspected separately. This bounded
pattern scan is not a professional penetration test or a guarantee of no possible secret.
No `.env`, access file, native DB/vector files, uploaded private PDFs, backups or models
are included in the commit.

Unresolved advisory evidence: [fresh OSV results](SECURITY_ADVISORIES.json),
[upstream critical advisory](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c).
Embedded fixed-model use excludes the exposed Chroma HTTP endpoints described there,
but the installed package is not patched. Do not waive the CI gate or call it secure.

## GitHub, deployment and cost boundaries

Push destination explicitly confirmed: `https://github.com/Dhroovs/YojanaSetu.git`,
`main`, no force push, no visibility change. The project push succeeded at `e02182777402ce5623d3c778f68e3b27cfa6f323`,
followed by runtime CI verification commit `5a0a1694d7cb94a3305938833f91b77b35a8eccb`.
Remote branch identity was checked after push. The final documentation-only commit
may follow these release commits; use `git rev-parse origin/main` for the current tip.

[FREE_HOSTING_REVIEW.md](FREE_HOSTING_REVIEW.md) compares official current restrictions.
Recommendation is complete local synthetic walkthrough plus the approved, clearly
labeled GitHub Pages screenshot/code showcase, now published and verified. It is not a mock backend or full hosted
application. No public backend/tunnel or external database was provisioned.

Architecture for a future full deployment remains frontend reverse proxy, FastAPI,
authenticated Mongo, embedded persistent Chroma, private files and separate durable
worker, with HTTPS/secrets/monitoring/backups. The supplied Compose file is a local
rehearsal, not a free hosted service or public-production configuration.

## Maintenance and next action

Use LOCAL_DEMO_ACCESS.md to inspect roles, LOCAL_SETUP_WINDOWS.md to start from a
stopped machine, TESTING.md for repeatable commands, and DEMO_SCRIPT.md for the narrative.
Keep the PC awake/online for local walkthroughs. Do not expose seeded admin credentials,
copy the demo database into production, disable the advisory gate, or remove source
limitations to make the interview look more complete.

Remaining external decisions: resolve
upstream Chroma risk before exposing the backend; obtain a genuinely suitable persistent
host or separately approve a future budget; test native speech and translations with
target users. Any paid provider/model/messaging action still needs separate approval.
No Phase 6 was started. The full functional local demo is available for inspection.


## Observed publication and remote verification

- Public showcase: **https://dhroovs.github.io/YojanaSetu/**, HTTPS enforced,
  GitHub Pages source main:/docs, build status built, HTTP 200.
- Live Chrome checks: 16 image HTTP 200 checks, four filter states, 390px mobile width,
  zero JavaScript errors, no login forms and no backend API calls.
- Full local application after restart: frontend, readiness and API docs all HTTP 200.
  Existing synthetic data and encrypted passwords were preserved; services are running.
- Initial public GitHub CI run 45233487891: frontend success, Linux container build
  success; backend 108 passed in 26.02s and pip consistency passed. The backend job then
  failed only at the unchanged Chroma advisory gate.
- Runtime CI run: https://github.com/Dhroovs/YojanaSetu/actions/runs/45315099259 .
  This run caught an HTTP 502 proxy recovery failure after restart. The proxy now
  refreshes Docker service DNS and the smoke test waits for proxy readiness, then also
  replaces backend/worker containers to verify recovery with changed service addresses.
  The corrected run is linked below; no failing assertion was removed.
- Static hosting and standard public-repository CI use the existing GitHub account;
  no card, paid trial, subscription, provider account or usage-based service was added.

The complete public application remains Blocked by External Dependency, independently
of the successful static publication. No live hosted model or messaging is implied.


## Final closure: 24 November 2026

- Verified code/runtime commit: **26c4af5**. Final documentation-only commit follows
  on main without changing application code; its exact tip is visible on GitHub.
- Final CI: https://github.com/Dhroovs/YojanaSetu/actions/runs/45315579098 .
  **Frontend: success. Containers: success. Backend: fails at the Chroma advisory gate
  after all 108 tests passed in 27.71s, lint/format and pip consistency pass.** Overall CI remains red
  deliberately; no advisory was suppressed.
- Linux container runtime is now **Verified Working** for four-service startup,
  same-origin frontend/API proxy, citizen registration/login, private-case access,
  admin denial, logout revocation, running worker sweeps, and Mongo/private-file/
  synthetic-vector persistence across restart and backend/worker replacement.
  This does not claim official-source RAG/model inference inside a fresh container,
  a full backup restore drill, or complete hosted production deployment.
- Local Docker remains absent. Verification used free standard GitHub-hosted Linux
  runners in the existing public repository, not a new cloud account or paid plan.
- Chroma remains the only package finding in the final 24 November OSV scan of 119 pins.
- The static HTTPS showcase is deployed and verified. The complete local platform is
  restarted and ready for inspection. No additional automatic work or Phase 6 is planned.


## Subsequent documentation and portfolio milestone

The 24 November portfolio pass expands README/source guides, 110 interview Q&As, 20 walkthrough chapters, quick revision, glossary, timed demo and resume material. A 22-slide Markdown deck, editable HTML and verified 22-page PDF are supplied; no PowerPoint export is claimed. Three additional real public discovery/language/mobile screenshots supplement the 16 release inspection captures. Application behavior is unchanged (environment-example edits are comments only). See [documentation QA](DOCUMENTATION_QUALITY.md); the 108/25 recorded execution counts above keep their dates and are not claimed as a new full regression run.
