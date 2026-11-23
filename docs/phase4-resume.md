# Phase 4 paused checkpoint — 23 November 2026

User requested a pause during final verification. Stop feature implementation here;
resume only when the user returns. Phase 4 is **partial**, not production-ready.
No deployment, push, purchase or paid model call was made.

## Completed foundation

Phase 3 closure was verified before Phase 4 and committed as `61702b8`.
See [Phase 3 closure](phase3-closure.md) for its exact results and limitations.

New SevaSetu code includes:

- Authenticated, owner-scoped requests with consent, location, service category,
  accessibility, language and preferred appointment window.
- Coordinator claim/review, worker profiles, administrator verification with expiry,
  declared calendars, organization API, eligibility filtering and workload ranking.
- Revision-checked, idempotent assignment with an atomic Mongo worker reservation.
  Assignment is a proposal until the worker accepts. Pending workers receive a
  redacted address. Concurrent conflicting assignments cannot both reserve a slot.
- Acceptance, decline, cancellation, rescheduling, en-route, check-in, recorded
  outcome, coordinator completion review, feedback and internal escalation actions.
  Visit completion never means government approval or official KYC.
- An eight-node Doorstep Coordinator LangGraph, read-only by default. Optional
  assignment uses the same authorized, confirmed service method as the API.
- Case orchestrator routing to all five task agents, including linked doorstep
  authorization. Doorstep guidance cannot silently create or mutate a booking.
- Durable in-app notice records, acknowledgement, missed/unaccepted assignment
  sweeps, calendar reconciliation, retention code and a generic case completion
  outbox. Existing `python -m app.cases.worker --once` also processes SevaSetu jobs.
- React request/dashboard/detail, worker availability and staff verification pages,
  linked from scheme results and private cases. The guidance button sends POST
  with JSON null for read-only guidance; an empty assignment object is rejected.
- Central English/Hindi/Telugu navigation dictionaries with persisted language
  preference and English fallback. Translation is deliberately partial.

## Verification at pause

- Before the last integration edits: full backend **79 passed in 76.67 seconds**
  against real loopback MongoDB, no skips.
- After integration edits: targeted SevaSetu and Phase 3 tests **35 passed in
  38.94 seconds**. This includes eight SevaSetu tests: validation, ownership,
  verification permissions, assignment acceptance/replay/conflicts/cancellation,
  concurrent booking protection, rescheduling/suspension, human-reviewed outcome,
  linked-case agent authorization and durable job/notification processing.
- Final frontend: **14 passed across 6 files**, ESLint passed, TypeScript passed
  through the production build, Vite build passed (**29 modules**).
- Phase 1–3 Chrome browser checks passed at the Phase 3 checkpoint. **The new
  SevaSetu browser workflow has not been run.** Do not equate a build with browser
  verification. New UI components also need dedicated interaction tests.
- Final full backend: **82 passed in 101.41 seconds**, against real MongoDB,
  no skipped tests. Ruff lint and format checks and `pip check` also passed.

## Remaining work by requested stage

| Stage | Status at pause | Remaining work |
| --- | --- | --- |
| A Phase 3 closure | Completed | Preserve checkpoint and prior evidence |
| B SevaSetu | Partial | Browser verification, profile update/reverification policy, organization management UI, consent/preferences editing, more transition and failure-recovery checks |
| C Five agents | Partial | Routing and authorization implemented/tested; full five-agent end-to-end scenario and broader adversarial tests remain |
| D LLM | Partial, pre-existing adapters | Add token/output bounds, bounded retries, explicit hosted-provider approval gate and grounding tests; no live local model has been verified |
| E Government sources | Deferred | Only existing PM-KISAN partial source is ingested; add reviewed central/Telangana sources, source coverage/freshness/conflict reporting |
| F Multilingual | Partial | Navigation dictionaries and notice templates exist; most forms and all scheme/legal explanations use English; no translation/voice provider |
| G Notifications | Partial | Durable SevaSetu notices/jobs added; further quiet-hour/frequency, retention and case-outbox replay tests needed; no SMS/email/WhatsApp |
| H Security | Partial | Ownership/roles/consent/CAS/calendar controls tested; complete new-surface privacy, abuse and verification-race audit |
| I/J Verification | Partial | Full regression and build checks recorded; new browser/multi-role/mobile/concurrency breadth remains |
| K Documentation | Partial | This resume record and Phase 3 handoff exist; final API guide, diagrams, requirement matrix and interview explanation remain |

## Known limitations to address first

1. Worker profile creation is implemented, but existing profiles are not materially
   editable. Organization creation/listing exists through API, not a full UI.
2. `override_reason` is accepted on assignments but is not yet a complete exceptional
   scheduling policy/audit path. Eligibility cannot be bypassed. Decide how a
   coordinator-proposed window differing from the citizen preference is consented.
3. Review worker access to cancelled/terminal historical requests and minimize
   retained address/description exposure. Cancellation currently retains worker ID.
4. Tighten individual string bounds in list fields and complete state-transition
   auditing. Some UI buttons are shown in states where the backend rejects them.
5. The old language notice/footer still needs reconciliation with partial SevaSetu
   and navigation implementation. Do not claim full translation or voice support.
6. More tests are needed for case completion outbox replay, reservation crash recovery,
   verification expiry races, localized notice content, quiet hours and retention.
7. No new official source was ingested. Research candidates were the Department of
   Financial Services PMSBY page and Telangana ePASS Kalyana Lakshmi portal. Review
   actual source text and conflicting conditions before creating any eligibility rules.
8. `SEVA_NOTIFICATION_INTERVAL_HOURS` defaults to 1 and `SEVA_RETENTION_DAYS` to 180
   in Settings; add these to `.env.example` in the documentation pass.

## Resume commands

Run from repository root in PowerShell, with local MongoDB on port 27017:

```powershell
$env:MONGO_TEST_URI='mongodb://127.0.0.1:27017'
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
.\backend\.venv\Scripts\python.exe -m ruff check backend/app backend/tests
.\backend\.venv\Scripts\python.exe -m ruff format --check backend/app backend/tests
.\backend\.venv\Scripts\python.exe -m pip check
```

For frontend commands, use the cached Node directory on PATH and run in `frontend`:

```powershell
$env:PATH='C:\Users\dhroo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
node ..\.tools\package\bin\npm-cli.js test
node ..\.tools\package\bin\npm-cli.js run lint
node ..\.tools\package\bin\npm-cli.js run build
```

Temporary browser scripts stop their own servers. The main frontend/backend were
not started at this pause. A pre-existing local MongoDB process may remain running;
do not kill unrelated processes or delete live data on resume.
