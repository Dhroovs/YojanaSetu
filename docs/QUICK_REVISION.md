# Quick revision: 15-20-minute study plan

This is a revision target, not a measured reading-time claim. Read source anchors in
[the full interview guide](INTERVIEW_GUIDE.md) when an answer feels unfamiliar.

## Five-minute emergency revision

- **Pitch:** reviewed welfare guidance connects to private assistance cases and consented doorstep help.
- **Architecture:** React -> FastAPI guards -> services/graphs -> Mongo operational records, private files and Chroma public evidence.
- **Five capabilities:** Scheme Matcher, Document Verifier, Follow-up, Escalation, Doorstep Coordinator. Three are deterministic case nodes, not separate autonomous LLMs.
- **RAG:** review source -> extract/chunk -> hash/version/embed -> retrieve active evidence -> curated checks -> validate citations -> preliminary answer. Partial sources can keep eligibility unknown.
- **Authentication:** salted scrypt; opaque hashed bearer sessions, expiry/current account/auth_version; no JWT. Roles still need object ownership/assignment.
- **Integrity:** current revision protects against stale writes; idempotency protects retries; one atomic worker calendar protects overlapping assignment.
- **Visit:** consent -> claim/review -> eligible proposal/confirmed assignment -> worker acceptance -> check-in/outcome -> coordinator review -> feedback/follow-up.
- **Truth:**108 backend / 25 frontend recorded tests, five browser suites and remote container persistence passed. Overall CI remains red at the Chroma advisory gate.
- **Deployment:** public Pages URL is a static showcase. Full backend remains local; live LLM, physical speech and external SMS/WhatsApp delivery are unverified/unconfigured.
- **Ownership:** explain your AI-assisted development and what you can independently trace. Never claim real citizens, accuracy percentages or government partnership.

## Fifteen-to-twenty-minute route

| Approximate focus | Revise | Prove it |
| --- | --- | --- |
| First 3 minutes | Problem, users and five-phase journey | Speak the 30-second introduction |
| Next 4 minutes | Architecture, RAG and two stores | Draw request -> evidence -> citation |
| Next 4 minutes | Sessions, roles, ownership and files | Explain one denied cross-account request |
| Next 4 minutes | Visit state, calendar races, CAS and retry | Describe two coordinators choosing one slot |
| Final 3 minutes | Test evidence, hosting limits and personal role | Explain one verified fix and one unresolved gate |

## Phases, stack and stores

1. Foundation: React/TypeScript/Vite, FastAPI/Pydantic and Mongo catalogue/intake.
2. Intelligence: reviewed sources, local ONNX/Chroma retrieval, rules/citations and graph.
3. Private cases: sessions/roles, Document/Follow-up/Escalation and durable human review.
4. SevaSetu: current verified worker matching, atomic calendars and visit lifecycle.
5. Integration: signup/admin, draft hi/te UI, consented voice fallback, notices/adapters, security/tests/containers/CI and static showcase.

Mongo contains exact operational truth and source metadata. Chroma contains public chunks/vectors.
Private bytes remain outside the public root. Graph state is ephemeral; no LangGraph checkpointer is configured.
Minimal matcher memory expires in Mongo. External providers are optional and approval-gated.

## Routes and source map

| Route / file | Remember |
| --- | --- |
| POST /api/auth/register, /api/auth/login | Citizen-only signup; expiring opaque bearer |
| GET /api/schemes, /api/ai/coverage | Public catalogue/provenance |
| POST /api/ai/scheme-match | Bearer plus independent X-Session-Key; no shared secret needed for valid login |
| POST /api/cases, /api/cases/{case_id}/assist | Owned case and bounded task intent |
| POST /api/seva/requests/{booking_id}/assignment | Confirmed human action plus current calendar authority |
| GET /api/admin/operations | Safe admin view, not arbitrary environment editing |
| frontend/src/auth.tsx | privateApi and memory-only session |
| backend/app/auth.py | current_actor, scrypt, expiry/revocation |
| backend/app/agents/scheme_matcher.py | Graph nodes, rules and citations |
| backend/app/cases/service.py | Authorized transitions, receipts and CAS |
| backend/app/seva/store.py | Atomic reserve filter |
| backend/app/cases/worker.py | Persisted jobs and polling |

## Top25 practice questions

### 1. What does YojanaSetu do?

It links scheme information to private assistance. React/FastAPI connect reviewed-source matching, checklist cases and consented visits. A PMSBY question can become a case with accountable next steps.

[Full answer/source](INTERVIEW_GUIDE.md)

### 5. Why retain human review?

Uncertain documents and sensitive actions need accountability. Checklist acceptance, assignment confirmation and visit completion are guarded human actions. A readable PDF is not automatically authentic.

[Full answer/source](INTERVIEW_GUIDE.md)

### 6. How is this different from a chatbot?

It maintains operational records and enforced workflows. A visit has persisted state, receipts and a calendar reservation rather than merely a chat promise. Model text cannot create authority.

[Full answer/source](INTERVIEW_GUIDE.md)

### 10. How should you describe AI-assisted development?

Explain assistance and your own understanding honestly. Separate generated implementation, reviewed decisions and tests you can explain. Demonstrate a source trace or calendar race instead of claiming manual authorship of every line.

[Full answer/source](INTERVIEW_GUIDE.md)

### 12. Trace a case creation click.

The form reaches a guarded service and database write. PrivateDashboard calls privateApi; POST /api/cases reaches CaseService.create and CaseStore.create. The response supplies a real case ID and revision.

[Full answer/source](INTERVIEW_GUIDE.md)

### 20. What happens after a hard refresh?

The memory-only login is lost. Bearer tokens are not retained in localStorage. Language persistence is separate. The user signs in again before loading private data.

[Full answer/source](INTERVIEW_GUIDE.md)

### 21. Why FastAPI?

Typed Python request boundaries fit the project. Pydantic validation, reusable dependencies and generated OpenAPI make API contracts explicit. This is retrospective engineering rationale rather than a benchmark against Flask/Django.

[Full answer/source](INTERVIEW_GUIDE.md)

### 26. How do you interpret API errors?

They identify different failure classes. 401 means invalid session,403 role denial,404 unavailable/unowned object,409 conflict,422 invalid input. A stale revision requires refresh, not blind overwrite.

[Full answer/source](INTERVIEW_GUIDE.md)

### 36. Why both MongoDB and Chroma?

They answer different questions. Mongo is exact operational truth; Chroma searches public evidence vectors by similarity. Case ownership cannot be inferred from vector proximity.

[Full answer/source](INTERVIEW_GUIDE.md)

### 40. How does backup/restore work?

Quiesce writers and restore into new targets. The CLI exports Mongo/index metadata and private/vector files, validates collection hashes and excludes sessions. The synthetic drill is not production disaster-recovery certification.

[Full answer/source](INTERVIEW_GUIDE.md)

### 41. What is RAG?

Retrieve evidence before explaining it. Reviewed chunks are embedded/retrieved, curated conditions evaluated and citations checked. Optional generation stays bounded by evidence. The verified mode is retrieval-only.

[Full answer/source](INTERVIEW_GUIDE.md)

### 46. What makes a citation traceable?

It carries the evidence location and identity. Citation fields include source/chunk IDs, URL, page, quote and hash. Active Mongo source versions must agree with retrieved Chroma metadata.

[Full answer/source](INTERVIEW_GUIDE.md)

### 48. How does missing information affect eligibility?

It remains explicit rather than being guessed. Rule outcomes are met/not_met/unknown. Partial/stale coverage can keep the overall result unknown even when known conditions match.

[Full answer/source](INTERVIEW_GUIDE.md)

### 53. What if the LLM is unavailable?

Preserve bounded evidence-only behavior when possible. Provider failures produce warnings/fallback. No relevant retrieval evidence still means cannot verify, not a model-generated guess. The demonstrated configuration is LLM_PROVIDER=none.

[Full answer/source](INTERVIEW_GUIDE.md)

### 59. RAG versus fine-tuning?

RAG looks up evidence; fine-tuning changes weights. This project ingests sources and embeds chunks without training a foundation model. Updating official content calls for review/re-ingestion rather than weight training.

[Full answer/source](INTERVIEW_GUIDE.md)

### 65. Why five assistance capabilities?

The tasks have different evidence and action boundaries. Matching, checklist assessment, reminders, referral and visits are separated so a text response cannot stand in for authorization or scheduling integrity.

[Full answer/source](INTERVIEW_GUIDE.md)

### 68. Are LangGraph checkpoints persisted?

No checkpointer is configured in these graphs. graph.compile() has no durable saver. Cases, visits, receipts/jobs and minimal matcher context survive separately; raw prompt/transcript checkpoints are not stored.

[Full answer/source](INTERVIEW_GUIDE.md)

### 69. How is human-in-the-loop enforced?

The backend requires an authorized confirmed action. Current role, revision, consent and confirmation guard assignment. A model saying approved is not sufficient. Worker acceptance follows coordinator proposal.

[Full answer/source](INTERVIEW_GUIDE.md)

### 78. How are duplicate reminders prevented?

Persistent identities and guarded writes decide delivery. A reminder references its follow-up ID, and CAS rejects competing stale saves. Retry processing is distinct from falsely promising exactly-once external transport.

[Full answer/source](INTERVIEW_GUIDE.md)

### 81. What makes a worker eligible?

Account, verification, scope and calendar must fit. The service checks current role/active state, expiry through visit end, category/language/area/capabilities, organization, capacity and overlap. A free slot alone is insufficient.

[Full answer/source](INTERVIEW_GUIDE.md)

### 84. How do you prevent double bookings?

One calendar document is the atomic conflict authority. SevaStore.reserve filters revision, current verification, capacity and overlapping reservations in one update. Competing overlapping writes cannot both win that authority.

[Full answer/source](INTERVIEW_GUIDE.md)

### 85. What is compare-and-swap?

Save only if the version still matches your read. Updates/replacements include revision in the filter. A stale operation returns409. This prevents a later stale form from silently erasing another actor's work.

[Full answer/source](INTERVIEW_GUIDE.md)

### 86. What is idempotency?

A repeated intended action must not repeat its effect. Operation keys and payload fingerprints distinguish valid replay from reuse with changed details. Creation uses unique owner/key authority rather than disabling a button.

[Full answer/source](INTERVIEW_GUIDE.md)

### 92. Do you use JWT?

No; these are opaque bearer sessions. Random tokens are hashed server-side and checked against expiry/current user/auth_version. Logout revokes the session; account changes invalidate old versions.

[Full answer/source](INTERVIEW_GUIDE.md)

### 99. Why is CI red with passing tests?

The dependency audit is an independent release gate. Chroma1.5.9 remains flagged. Embedded fixed-model use narrows exposure but does not patch the package. The backend job stops at OSV after passing its tests/checks.

[Full answer/source](INTERVIEW_GUIDE.md)

## Vocabulary to explain aloud

API: request boundary. RAG: evidence lookup plus bounded explanation. Embedding: numeric text representation.
RBAC: role permission. Object authorization: this actor's right to this record. CAS: revision-guarded update.
Idempotency: safe intended replay. Durable job: persisted due work. TTL: eventual cleanup plus explicit runtime expiry.
Human-in-the-loop: authenticated review/confirmation, not a model's promise. [Full glossary](GLOSSARY.md).

## Evidence and limitations

Local backend 108 passed in 155.43s and frontend 25 passed on 23 November 2026; Linux108 passed in 27.71s
on 24 November. Counts are historical verified evidence, not a claim that every future checkout is green.
Frontend/container CI passed; the Chroma audit remains failing. Three schemes/four partial sources,
draft translations, no certified hi/te retrieval, unverified native speech/live models, unconfigured paid
messaging, missing recovery/MFA and production scale/restore review remain explicit limits.
[Exact release](FINAL_RELEASE_REPORT.md) and [free hosting](FREE_HOSTING_REVIEW.md).
