# Explaining YojanaSetu + SevaSetu

“We built a local full-stack welfare information and assistance platform. React calls
FastAPI; MongoDB holds authorized case and visit state, while Chroma retrieves reviewed
official-source evidence with local embeddings. Five bounded agent workflows help
match schemes, check document readiness, schedule follow-ups, recommend escalation,
and coordinate in-person assistance. Humans approve consequential actions.”

## Why LangGraph?

Each workflow has explicit nodes and typed state, so retrieval, validation, ranking
and human approval are visible and testable. It supports asynchronous composition
without giving a language model arbitrary database or network tools. It does not
make these agents autonomous government decision makers. Durable state is persisted
as domain records and receipts rather than raw model conversations.

## How does RAG prevent unsupported claims?

Only reviewed official-source chunks from active content-hash/index versions are
returned. Curated rules require exact source evidence; numeric thresholds must appear
in their quote. Citations are checked against chunk text, source ID, URL, hash and
page. An optional model selects existing excerpts instead of writing new government
claims. Partial information yields uncertainty, not an invented positive decision.
RAG alone cannot establish that an old official page remains legally current.

## Why deterministic eligibility and assignment?

Rules such as reviewed age boundaries and worker calendar conflicts are reproducible
constraints. An LLM must not guess them. Assignment first filters authorization,
coverage, language, accessibility, declared availability and capacity, then ranks
eligible workers by workload. A coordinator can choose a lower ranked eligible
worker with an audited reason; suspension or conflict cannot be overridden.

## How do human gates work?

Administrators review worker verification and expiry. Coordinators approve requests
and assignment proposals. Workers accept before appointments are confirmed, record
performed services and tasks, and submit outcomes for coordinator review. Citizens
can report problems, confirm receipt, give feedback, withdraw sharing or request
follow-up. Every relevant change is authorized and attributed. A visit is internal
assistance, not official approval, KYC or scheme submission.

## Why MongoDB and Chroma?

MongoDB supports indexed operational records, compare-and-swap revisions, unique
idempotency keys and durable job schedules. One atomic worker calendar document
prevents overlapping reservations even on standalone MongoDB. Chroma is specialized
for semantic source retrieval; it is not the authority for ownership or case status.

## How are retries and failures handled?

Request creation and lifecycle mutations have idempotency receipts; stale or changed
replays return conflict. The optional model has bounded timeouts, output size, tokens
and retry count, with deterministic fallback. Multi-document booking updates can
leave a conservative held reservation after a crash; recovery requires proof from
booking revision/state before releasing it. A completion outbox emits a generic case
activity exactly once using a receipt. Durable polling is required for background work.

## How is privacy enforced?

Individual scrypt-backed accounts receive opaque sessions stored hashed server-side.
Roles and object ownership are checked on each request. Workers receive only assigned
visits, with exact location withheld before acceptance; terminal requests are denied.
Documents stay outside the public web root. Notification templates contain no private
documents or addresses. Retention removes sensitive visit free text and private case
documents. Prompt tracing is disabled. Optional model summaries receive minimal
authorized facts. No biometric, Aadhaar authentication or covert tracking is implemented.

## What remains before production?

This has local automated/browser verification, not a production deployment. Live LLM
inference is unverified because no local server was available and paid calls were not
authorized. Only three partial official sources are indexed. Hindi/Telugu support is
partial; voice and external messaging are disabled. Production also needs secure
infrastructure, staff onboarding/governance, backup/restore, monitoring, load/failure
testing, legal/privacy review, broader current source coverage and reviewed translations.
