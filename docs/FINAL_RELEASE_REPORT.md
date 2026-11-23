# Final demonstration and release report

Verification date: 23 November 2026. Baseline: `f631208`.
Repository confirmed by owner: https://github.com/Dhroovs/YojanaSetu, branch `main`,
existing public visibility unchanged. Repository API confirms push permission; no
unrelated remote branches/commits were present during preparation.

**Overall: Verified Working locally; complete public backend deployment is Blocked
by External Dependency.** No complete live application URL is claimed. Publication
of a separate static interview showcase is awaiting the owner's answer. No paid plan,
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
| Ruff lint/format | Verified Working | All checks passed; 69 files formatted |
| Python package consistency | Verified Working | No broken requirements found |
| npm audit | Verified Working | 0 vulnerabilities; 334 dependencies reported |
| Python OSV audit | Blocked by External Dependency | Exit 1; chromadb1.5.9 has four GHSA findings plus four PYSEC aliases; 119 packages scanned |
| Existing browser suites | Verified Working | All five scripts passed, zero JS page errors |
| Real-source integration | Verified Working | PMSBY/Kalyana Lakshmi retrieval and citations; coverage3schemes/4sources; no LLM called |
| Persistent demo browser inspection | Verified Working | **16 screenshots**, real RAG/reminder/admin mutation and auth isolation; zero JS errors |
| Simulated completed-visit fixture | Verified Working | Real API acceptance/en-route/check-in/outcome/human review/feedback persisted; explicitly no real service |
| Local Docker/Compose runtime | Not Tested | Docker not installed at normal path or on PATH; YAML parsed previously |
| Live Ollama/hosted LLM | Not Tested | Local `/api/tags` connection failed; hosted calls remain disabled |
| Native microphone/playback | Not Tested | Mocked consent/controls and real unsupported-browser fallback only |

The earlier 107-test run passed in149.60s before the new demo-only account regression
was added. The final108 count supersedes it. Browser suites are
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
| Complete public hosted platform | Blocked by External Dependency | No reviewed no-card INR0 host meets current worker/persistence needs; Chroma advisory also blocks public backend release |

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
`main`, no force push, no visibility change. Final push verification and remote CI
outcomes will be appended after execution; no success is inferred before then.

[FREE_HOSTING_REVIEW.md](FREE_HOSTING_REVIEW.md) compares official current restrictions.
Recommendation is complete local synthetic walkthrough plus, if approved, a clearly
labeled GitHub Pages screenshot/code showcase. It is not a mock backend or full hosted
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

Remaining external decisions: approve the separate static showcase if desired; resolve
upstream Chroma risk before exposing the backend; obtain a genuinely suitable persistent
host or separately approve a future budget; test native speech and translations with
target users. Any paid provider/model/messaging action still needs separate approval.
No Phase6 was started. The full functional local demo is available for inspection.
