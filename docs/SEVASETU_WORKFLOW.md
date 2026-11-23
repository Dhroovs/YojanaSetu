# SevaSetu workflow and authority

Citizens request a category, optional scheme/case, preferred time, location, language,
accessibility/caregiver needs and necessary sharing consent. Contact is in-app only.
Coordinates are optional API fields with separate explicit consent. No identity image,
Aadhaar, OTP, bank login, visit photo or covert location history is required.

```mermaid
stateDiagram-v2
  [*] --> PendingReview
  PendingReview --> Approved: coordinator reviews
  PendingReview --> Rejected: reason recorded
  Approved --> WorkerAssigned: confirmed eligible proposal
  WorkerAssigned --> Scheduled: worker accepts
  WorkerAssigned --> Unavailable: decline or timeout
  Scheduled --> InProgress: time-gated check-in
  Scheduled --> EnRoute: optional progress
  EnRoute --> InProgress
  InProgress --> OutcomeReview: actual services and tasks
  OutcomeReview --> Completed: coordinator review
  Completed --> FollowUp: requested future task
  Completed --> Closed: confirmed closure
  FollowUp --> Closed
  Scheduled --> Rescheduling: confirmed request
  Rescheduling --> WorkerAssigned: approval and renewed acceptance
  Scheduled --> NoShow: overdue not-started visit
  Scheduled --> Cancelled: confirmed cancellation
  Completed --> Escalated: disputed completion
  Escalated --> OutcomeReview: human resolution
```

```mermaid
flowchart TD
  Request[Reviewed request and citizen-confirmed window] --> Eligible[Current account, verification, expiry and organization]
  Eligible --> Coverage[Category, district or area, language, accessibility]
  Coverage --> Available[Declared availability, capacity, no overlap]
  Available --> Ranking[Workload then stable ID]
  Ranking --> Coordinator[Human selects and confirms]
  Coordinator --> Override[Audit reason for lower ranked eligible choice]
  Override --> Reserve[Atomic worker calendar reservation]
  Reserve --> CAS[Booking revision CAS and receipt]
  CAS --> Acceptance[Worker acceptance before confirmation]
```

Overrides cannot bypass eligibility or conflicts. Workers receive only assigned
requests; precise location is withheld before acceptance and outside active stages.
Terminal worker access is denied. A language change or consent withdrawal can revoke
an active assignment. Rescheduling never bypasses initial review. Recorded outcomes
cannot be erased by cancellation/rescheduling after a dispute; human review is required.

MongoDB's atomic worker document is the reservation authority. Standalone Mongo does
not make worker/calendar and booking updates one transaction. A crash may temporarily
hold capacity; reconciliation releases only when booking revision/state proves an
in-flight update cannot still commit. UTC seconds are stored; Asia/Kolkata is displayed.
The polling worker handles acceptance timeout, missed visits, notices and retention.

Administrators review workers, expiry and external-authorization evidence. Internal
verification is not government certification. Material profile changes reset it;
future reserved visits must be resolved before eligibility edits. Staff queues expose
actual records and workload, not fake metrics. Visit completion adds one generic case
activity/notice through an idempotent outbox; official case approval never changes.

Exact endpoints and role boundaries are in [API_REFERENCE.md](API_REFERENCE.md).
The Phase 4 Chrome workflow and Mongo concurrency tests demonstrate the full role path.
