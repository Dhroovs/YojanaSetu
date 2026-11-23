# Interview overview and technical questions

YojanaSetu discovers evidence-backed welfare information; SevaSetu coordinates internal
in-person assistance. React/TypeScript calls FastAPI, MongoDB persists authorized state,
and local Chroma/ONNX embeddings retrieve reviewed government evidence. Five bounded
agent workflows assist citizens while humans approve consequential changes.

## Questions and answers

**Why LangGraph?** Explicit typed nodes make routing, retrieval, validation and human
gates testable. The model does not receive a general tool executor. Domain state,
receipts, schedules and audit are durable; raw conversational graph checkpoints are not.

**Why MongoDB and Chroma?** MongoDB is the authority for users, cases, visits, calendars
and active source versions. Chroma serves semantic search over public reviewed text.
It is local, not an exposed multi-tenant server. The unresolved package advisory is
an honest release gate, not something to hide behind passing unit tests.

**How does RAG limit hallucination?** Sources have provenance, hashes/versions and exact
quote evidence. Curated numeric rules are deterministic. Citations are checked against
the active chunk URL/hash/page/text. Optional models select known excerpts/facts. Partial
or conflicting information produces uncertainty, not an invented entitlement.

**How are workers selected?** Current account/verification/expiry and organization,
geography, category, language, accessibility, availability and workload are checked
before ranking. Coordinators choose/confirm; lower ranked eligible choices need an
audit reason. Workers accept before appointments are confirmed. Constraints cannot
be bypassed by an LLM or an override.

**How do you prevent double booking and duplicate actions?** One atomic worker document
checks reservations/capacity and version. Booking/case CAS plus idempotency receipts
reject stale or changed replays. Conservative crash recovery may temporarily hold a
slot but releases it only with proof the pending booking update cannot still commit.

**How do privacy and RBAC work?** Scrypt passwords, hashed opaque sessions, fresh role
and auth-version checks, object ownership, assigned-worker visibility, redacted locations,
private file storage, generic notifications and retention. React escapes text. Request
logs exclude payloads; hosted models and external messaging are disabled by default.

**What does Document Verifier really verify?** Format, size, local readability and source
checklist progress. Humans accept assistance items. It does not prove authenticity,
identity, official eligibility or KYC. Optional OCR gracefully falls back if unavailable.

**What was tested?** Unit/API tests, real Mongo role/CAS/concurrency tests, actual local
RAG/citation smoke checks, five Chrome workflows, localization and voice fallback,
and a synthetic backup/new-target restore drill. Exact counts are in FINAL_HANDOFF.md.

**Is it production-ready?** It is a tested local candidate with explicit gates: unresolved
Chroma advisories, no Docker runtime/remote CI verification, no live LLM/native speech
verification, partial sources, draft translations and further security/operations review.
No deployment, paid call or government partnership is claimed.

**What would you do next?** Resolve upstream security gates, run container/Linux CI and
full restore drills, broaden reviewed sources/checklists, validate a local model and
native speech, and conduct language/accessibility/security review before deployment.
These are remaining Phase 5 acceptance actions, not a new Phase 6.
