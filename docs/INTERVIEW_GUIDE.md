# Interview preparation guide

This is a source-reading and speaking guide for the implemented project. It contains 110 distinct
questions, not a promise of production experience. Test evidence is dated in
[FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md). The public URL is a static showcase.

## Speaking introductions

### 30-second introduction

"YojanaSetu helps users find reviewed welfare-scheme information and manage private assistance cases.
SevaSetu adds coordinated doorstep help. I used React, FastAPI, MongoDB and controlled LangGraph
workflows with local document retrieval. Source citations, ownership checks, human review and
conflict-safe scheduling are the important safeguards. The full synthetic demonstration runs locally."

### 60-second introduction

Use the 30-second introduction, then add: "The matcher retrieves official passages with local ONNX
embeddings and Chroma, evaluates curated conditions and keeps unknown information explicit.
Documents need human checklist review. A separate worker handles durable reminders. Assignment
checks current verification, area, language and availability before an atomic calendar reservation.
Unresolved Chroma advisories still block a public backend, so the public page is an honest evidence showcase."

### Two-minute explanation

Follow a synthetic PMSBY question through retrieved passages and uncertain eligibility. Explain the
private case, source-backed checklist, synthetic PDF, human review, reminder and referral. Then explain
consent, assignment, worker acceptance/check-in, reviewed completion and feedback. Finish with the split
between Mongo operational truth and Chroma public evidence. Five capabilities do not mean five autonomous LLMs.

### Five-minute technical explanation

Spend 45 seconds on the problem,60 on UI/API/session boundaries,60 on RAG,75 on state/integrity,
30 on tests and30 on limitations. Show one actual source function for each major claim. Explain
CAS/idempotency using a retry or calendar race. Describe your AI-assisted development and review honestly.

### Detailed architecture explanation

React sends JSON plus a memory-only opaque bearer. FastAPI validates input and resolves a current actor.
Services enforce object ownership, transition legality and confirmations. Graphs orchestrate fixed tasks
through these services. Mongo holds records, receipts, audit and due jobs. Private files remain outside
the static root. Chroma contains public reviewed vectors. The polling worker resumes durable jobs.
Optional provider protocols do not become live integrations because their mocked tests passed.

## How to practice

Read the simple answer aloud, then explain the technical answer without jargon. Open the linked source
and trace one branch or record. Use the likely follow-up to test your understanding. Comparative
technology explanations are retrospective unless history documents the original choice.


## Project and ownership

### Q1. What does YojanaSetu do?

**Simple answer:** It links scheme information to private assistance.

**Technical answer:** React/FastAPI connect reviewed-source matching, checklist cases and consented visits. A PMSBY question can become a case with accountable next steps.

**Project example:** A synthetic PMSBY question becomes a private checklist case and a linked visit.

**Likely follow-up:** Which parts are publicly hosted?

**Implementation:** [backend/app/main.py](../backend/app/main.py)

### Q2. Why add SevaSetu?

**Simple answer:** Information alone does not complete practical assistance.

**Technical answer:** Separate visit services reuse case ownership and authentication, then coordinate consent, verified workers and human-reviewed outcomes.

**Likely follow-up:** Does completing a visit approve a benefit?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)

### Q3. Who is the intended user?

**Simple answer:** Citizens needing guidance and staff coordinating help.

**Technical answer:** Rural, elderly and less digitally confident users motivate readable controls, language preferences and human support. No adoption study is claimed.

**Likely follow-up:** How would you evaluate impact ethically?

**Implementation:** [frontend/src/main.tsx](../frontend/src/main.tsx)

### Q4. What problem does this solve?

**Simple answer:** It organizes evidence and continuity across assistance steps.

**Technical answer:** Search, citations, private case history, durable reminders and assignment connect tasks that a single answer cannot complete.

**Likely follow-up:** What impact has actually been measured?

**Implementation:** [backend/app/cases/service.py](../backend/app/cases/service.py)

### Q5. Why retain human review?

**Simple answer:** Uncertain documents and sensitive actions need accountability.

**Technical answer:** Checklist acceptance, assignment confirmation and visit completion are guarded human actions. A readable PDF is not automatically authentic.

**Project example:** A technically readable PDF still needs human checklist acceptance.

**Likely follow-up:** What can an agent change without approval?

**Implementation:** [backend/app/cases/service.py](../backend/app/cases/service.py)

### Q6. How is this different from a chatbot?

**Simple answer:** It maintains operational records and enforced workflows.

**Technical answer:** A visit has persisted state, receipts and a calendar reservation rather than merely a chat promise. Model text cannot create authority.

**Likely follow-up:** What survives a server restart?

**Implementation:** [backend/app/seva/store.py](../backend/app/seva/store.py)

### Q7. How do the phases connect?

**Simple answer:** Each extends an existing working layer.

**Technical answer:** Foundation led to reviewed RAG, secure case agents, doorstep coordination and integration/verification. Phase 4 reused Phase 3 sessions.

**Likely follow-up:** Which legacy development paths remain?

**Implementation:** [docs/PHASE5_COMPLETION_MATRIX.md](../docs/PHASE5_COMPLETION_MATRIX.md)

### Q8. What is genuinely verified?

**Simple answer:** The bounded local platform and recorded checks.

**Technical answer:** Evidence documents108 backend tests,25 frontend tests, five browser scripts and remote container persistence. Public backend release remains blocked.

**Project example:** The release records 108/25 tests while the advisory gate stays red.

**Likely follow-up:** Why is overall CI red?

**Implementation:** [docs/FINAL_RELEASE_REPORT.md](../docs/FINAL_RELEASE_REPORT.md)

### Q9. Can you claim real social impact?

**Simple answer:** Only intended benefits, without invented adoption metrics.

**Technical answer:** There is no verified citizen count, production usage or field impact study. Synthetic demonstrations show technical behavior rather than social outcomes.

**Likely follow-up:** What would a responsible pilot measure?

**Implementation:** [docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md)

### Q10. How should you describe AI-assisted development?

**Simple answer:** Explain assistance and your own understanding honestly.

**Technical answer:** Separate generated implementation, reviewed decisions and tests you can explain. Demonstrate a source trace or calendar race instead of claiming manual authorship of every line.

**Project example:** Open SevaStore.reserve and explain the overlap filter yourself.

**Likely follow-up:** Which component can you explain independently?

**Implementation:** [docs/FINAL_HANDOFF.md](../docs/FINAL_HANDOFF.md)


## Frontend

### Q11. What is the frontend/backend boundary?

**Simple answer:** The browser presents choices and the server enforces rules.

**Technical answer:** React sends HTTP JSON requests. FastAPI resolves actors, validates bodies and calls services. Browser state cannot establish ownership.

**Likely follow-up:** Why is hiding a button insufficient?

**Implementation:** [frontend/src/main.tsx](../frontend/src/main.tsx)

### Q12. Trace a case creation click.

**Simple answer:** The form reaches a guarded service and database write.

**Technical answer:** PrivateDashboard calls privateApi; POST /api/cases reaches CaseService.create and CaseStore.create. The response supplies a real case ID and revision.

**Project example:** PrivateDashboard sends POST /api/cases; the service derives owner_id from the actor.

**Likely follow-up:** Where is owner_id assigned?

**Implementation:** [frontend/src/private-cases.tsx](../frontend/src/private-cases.tsx)

### Q13. Why separate API, service and store?

**Simple answer:** Each has a distinct responsibility.

**Technical answer:** Routes handle transport/validation, services enforce domain actions, and stores implement guarded persistence. Graphs reuse services rather than duplicate authority.

**Likely follow-up:** Could a graph bypass authorization?

**Implementation:** [backend/app/cases/service.py](../backend/app/cases/service.py)

### Q14. Why React rather than plain JavaScript?

**Simple answer:** Stateful reusable screens benefit from components.

**Technical answer:** Auth/language providers and shared form patterns reduce repeated DOM logic. This is retrospective rationale, not a proven historical comparison study.

**Likely follow-up:** What overhead does React add?

**Implementation:** [frontend/src/auth.tsx](../frontend/src/auth.tsx)

### Q15. Why TypeScript?

**Simple answer:** It catches mismatched data use during development.

**Technical answer:** Interfaces describe props and response use. Runtime Pydantic validation still matters because TypeScript does not validate hostile network data.

**Likely follow-up:** Where can an interface become stale?

**Implementation:** [frontend/src/private-cases.tsx](../frontend/src/private-cases.tsx)

### Q16. What does Vite do?

**Simple answer:** It supplies local development and bundling.

**Technical answer:** npm run build runs tsc -b and Vite. VITE_API_BASE_URL becomes browser-visible build configuration, so it must not contain credentials.

**Likely follow-up:** When must a frontend environment change be rebuilt?

**Implementation:** [frontend/package.json](../frontend/package.json)

### Q17. How is Tailwind used?

**Simple answer:** Base/utilities coexist with substantial custom CSS.

**Technical answer:** styles.css includes Tailwind directives, plus application layouts, focus indicators, touch targets and reduced-motion rules. It is not an all-utility design.

**Likely follow-up:** How do you verify accessibility?

**Implementation:** [frontend/src/styles.css](../frontend/src/styles.css)

### Q18. Where is frontend state managed?

**Simple answer:** Component hooks and auth/language contexts.

**Technical answer:** useState/useEffect manage records, loading and errors. No Redux store is introduced. Session results also guard against responses owned by a previous login.

**Project example:** A late matcher response from a signed-out login cannot populate the next login.

**Likely follow-up:** How are late responses rejected?

**Implementation:** [frontend/src/session-results.ts](../frontend/src/session-results.ts)

### Q19. How are private pages protected?

**Simple answer:** UI gates aid navigation; server checks provide security.

**Technical answer:** Components use auth state and privateApi, but every relevant API operation checks actor and object authority. Direct admin requests from citizens fail.

**Likely follow-up:** What if browser JavaScript is modified?

**Implementation:** [backend/app/admin.py](../backend/app/admin.py)

### Q20. What happens after a hard refresh?

**Simple answer:** The memory-only login is lost.

**Technical answer:** Bearer tokens are not retained in localStorage. Language persistence is separate. The user signs in again before loading private data.

**Project example:** Reload a private page and sign in again; the language preference can remain.

**Likely follow-up:** What usability trade-off does this make?

**Implementation:** [frontend/src/auth.tsx](../frontend/src/auth.tsx)


## Backend and HTTP

### Q21. Why FastAPI?

**Simple answer:** Typed Python request boundaries fit the project.

**Technical answer:** Pydantic validation, reusable dependencies and generated OpenAPI make API contracts explicit. This is retrospective engineering rationale rather than a benchmark against Flask/Django.

**Likely follow-up:** When would a larger framework help?

**Implementation:** [backend/app/main.py](../backend/app/main.py)

### Q22. What does Pydantic validate?

**Simple answer:** Structure, allowed fields and constraints.

**Technical answer:** Strict models reject extra fields and constrain lengths, enums and timezone-aware windows. Public registration cannot request an admin role.

**Likely follow-up:** Does validation replace authorization?

**Implementation:** [backend/app/cases/models.py](../backend/app/cases/models.py)

### Q23. What is REST-style API design here?

**Simple answer:** Resources and guarded actions over HTTP.

**Technical answer:** JSON routes use methods/statuses to distinguish reads, creation and transitions. Some mutations are explicit POST actions rather than resource replacement.

**Likely follow-up:** Would a different API style be reasonable?

**Implementation:** [backend/app/seva/api.py](../backend/app/seva/api.py)

### Q24. GET versus POST in this app?

**Simple answer:** GET reads; POST creates or submits actions.

**Technical answer:** GET /api/schemes reads the catalogue; POST /api/seva/requests creates an owned request with 201. Mutations carry revisions/keys where required.

**Likely follow-up:** Should a GET assign a worker?

**Implementation:** [backend/app/main.py](../backend/app/main.py)

### Q25. Are PUT and PATCH implemented?

**Simple answer:** No PUT/PATCH/DELETE routes are currently exposed.

**Technical answer:** They are useful HTTP concepts but should not be invented in the reference. Role changes use POST /api/admin/users/{user_id}.

**Likely follow-up:** How could the API evolve compatibly?

**Implementation:** [backend/app/admin.py](../backend/app/admin.py)

### Q26. How do you interpret API errors?

**Simple answer:** They identify different failure classes.

**Technical answer:** 401 means invalid session,403 role denial,404 unavailable/unowned object,409 conflict,422 invalid input. A stale revision requires refresh, not blind overwrite.

**Likely follow-up:** Why hide an unowned object's existence?

**Implementation:** [backend/app/cases/api.py](../backend/app/cases/api.py)

### Q27. Why asynchronous Python?

**Simple answer:** Database/network waits can yield to other requests.

**Technical answer:** Async PyMongo handles I/O. Blocking embedding work is moved to a thread where implemented. Async alone does not parallelize CPU-heavy computation.

**Likely follow-up:** What could block the event loop?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q28. What is CORS?

**Simple answer:** A browser cross-origin access rule.

**Technical answer:** Configured origins and headers allow the local frontend to call FastAPI. It does not authenticate users and cannot stop a direct HTTP client.

**Likely follow-up:** Why is CORS not an access-control substitute?

**Implementation:** [backend/app/main.py](../backend/app/main.py)

### Q29. How do you inspect the API contract?

**Simple answer:** Use local /docs and OpenAPI.

**Technical answer:** create_app().openapi() exposes current methods, paths and schemas. Documentation inventory is checked against that actual contract, not a plan.

**Likely follow-up:** What ownership rules are absent from schemas?

**Implementation:** [backend/app/main.py](../backend/app/main.py)

### Q30. Why run a separate background worker?

**Simple answer:** Jobs should continue without an open browser.

**Technical answer:** app.cases.worker polls durable case/visit schedules. A browser timer would disappear on reload and would not provide server-side retry authority.

**Likely follow-up:** What happens during worker downtime?

**Implementation:** [backend/app/cases/worker.py](../backend/app/cases/worker.py)


## Databases and persistence

### Q31. What is a Mongo document?

**Simple answer:** A structured BSON record with fields and nested values.

**Technical answer:** A case embeds document metadata, reminders and activity. Application IDs are distinct from Mongo's internal _id and do not encode personal identity.

**Likely follow-up:** What are embedded-array limits?

**Implementation:** [backend/app/cases/models.py](../backend/app/cases/models.py)

### Q32. Which Mongo collections matter?

**Simple answer:** Users, sessions, cases, visits, calendars and evidence metadata.

**Technical answer:** assistance_cases and seva_requests hold operations; seva_workers holds availability/reservations; schemes and ai_sources describe catalogue provenance.

**Likely follow-up:** Are notices separate collections?

**Implementation:** [docs/DATABASE.md](../docs/DATABASE.md)

### Q33. Why use unpredictable IDs?

**Simple answer:** They avoid obvious identity leakage and collisions.

**Technical answer:** Random IDs and file keys help, but owner/coordinator/worker filters still enforce access. Knowing a valid case ID does not grant permission.

**Likely follow-up:** Why is secrecy of an ID insufficient?

**Implementation:** [backend/app/cases/store.py](../backend/app/cases/store.py)

### Q34. Why create database indexes?

**Simple answer:** To support lookup and enforce uniqueness.

**Technical answer:** Unique alias/session/case/owner-creation-key indexes protect invariants. Due-time indexes support polling. An index does not replace lifecycle authorization.

**Likely follow-up:** Which race does a unique creation key prevent?

**Implementation:** [backend/app/cases/store.py](../backend/app/cases/store.py)

### Q35. Does TTL instantly expire a session?

**Simple answer:** No; cleanup can be delayed.

**Technical answer:** Runtime session lookup requires expires_at greater than now, so expired tokens fail before Mongo's TTL deletion runs.

**Likely follow-up:** Which other records use TTL?

**Implementation:** [backend/app/auth.py](../backend/app/auth.py)

### Q36. Why both MongoDB and Chroma?

**Simple answer:** They answer different questions.

**Technical answer:** Mongo is exact operational truth; Chroma searches public evidence vectors by similarity. Case ownership cannot be inferred from vector proximity.

**Project example:** Mongo checks owner_id while Chroma searches official text.

**Likely follow-up:** Could Atlas Vector Search replace part of this split?

**Implementation:** [backend/app/ai/vectors.py](../backend/app/ai/vectors.py)

### Q37. Where are private document bytes?

**Simple answer:** In private filesystem storage, outside the public frontend.

**Technical answer:** Mongo keeps random storage keys and review metadata. An authorized content endpoint mediates access rather than publishing static file URLs.

**Likely follow-up:** What must a consistent backup include?

**Implementation:** [backend/app/cases/storage.py](../backend/app/cases/storage.py)

### Q38. Is Chroma a public server here?

**Simple answer:** No; it uses an embedded PersistentClient.

**Technical answer:** VectorIndex disables anonymized telemetry and supplies embeddings explicitly. Compose exposes no Chroma port. This limits advisory exposure but does not patch the package.

**Likely follow-up:** Why is the advisory gate still failing?

**Implementation:** [backend/app/ai/vectors.py](../backend/app/ai/vectors.py)

### Q39. Why store embedding identity?

**Simple answer:** Vectors must be produced by comparable models.

**Technical answer:** Collection metadata records provider/model identity. A mismatch rejects reuse and needs a new collection/re-ingestion, even if text remains unchanged.

**Likely follow-up:** What if vector dimensions change?

**Implementation:** [backend/app/ai/vectors.py](../backend/app/ai/vectors.py)

### Q40. How does backup/restore work?

**Simple answer:** Quiesce writers and restore into new targets.

**Technical answer:** The CLI exports Mongo/index metadata and private/vector files, validates collection hashes and excludes sessions. The synthetic drill is not production disaster-recovery certification.

**Likely follow-up:** Why refuse nonempty restore targets?

**Implementation:** [backend/scripts/backup.py](../backend/scripts/backup.py)


## RAG and provenance

### Q41. What is RAG?

**Simple answer:** Retrieve evidence before explaining it.

**Technical answer:** Reviewed chunks are embedded/retrieved, curated conditions evaluated and citations checked. Optional generation stays bounded by evidence. The verified mode is retrieval-only.

**Likely follow-up:** Can useful RAG operate without live generation?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q42. What is an embedding?

**Simple answer:** A numerical text representation for comparison.

**Technical answer:** Local ONNX all-MiniLM-L6-v2 maps questions and chunks to the same vector space. Similarity helps retrieve passages, but does not prove truth.

**Likely follow-up:** Does a vector represent eligibility?

**Implementation:** [backend/app/ai/providers.py](../backend/app/ai/providers.py)

### Q43. Why split documents into chunks?

**Simple answer:** To retrieve relevant passages with manageable context.

**Technical answer:** chunk_document defaults to 1100 characters and200 overlap, retaining page/source/version metadata. Chunk size is characters, not model tokens.

**Likely follow-up:** What if a supporting quote spans a boundary?

**Implementation:** [backend/app/ai/ingestion.py](../backend/app/ai/ingestion.py)

### Q44. What is semantic similarity?

**Simple answer:** Matching meaning-like text patterns rather than only exact words.

**Technical answer:** Chroma uses cosine distance with bounded top-k/distance filtering. A close insurance passage can still be incomplete or outdated.

**Likely follow-up:** How do precision and recall differ here?

**Implementation:** [backend/app/ai/vectors.py](../backend/app/ai/vectors.py)

### Q45. How are official sources admitted?

**Simple answer:** An operator reviews provenance and content before ingestion.

**Technical answer:** The CLI enforces official HTTPS hosts, redirect/public-IP/type/size/page restrictions and quote-backed fields. Ordinary matching requests cannot fetch arbitrary URLs.

**Likely follow-up:** Does an official hostname prove completeness?

**Implementation:** [backend/app/ai/ingestion.py](../backend/app/ai/ingestion.py)

### Q46. What makes a citation traceable?

**Simple answer:** It carries the evidence location and identity.

**Technical answer:** Citation fields include source/chunk IDs, URL, page, quote and hash. Active Mongo source versions must agree with retrieved Chroma metadata.

**Likely follow-up:** What invalidates old evidence after re-ingestion?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q47. How is source freshness evaluated?

**Simple answer:** Known dates are compared with a configured age window.

**Technical answer:** Both reviewed_at and known published_at can matter. Unknown publication dates and old sources produce warnings and withheld certainty.

**Likely follow-up:** Can the system detect a policy change automatically?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q48. How does missing information affect eligibility?

**Simple answer:** It remains explicit rather than being guessed.

**Technical answer:** Rule outcomes are met/not_met/unknown. Partial/stale coverage can keep the overall result unknown even when known conditions match.

**Likely follow-up:** How is unknown different from excluded?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q49. What if a scheme has multiple sources?

**Simple answer:** Preserve evidence and require reconciliation.

**Technical answer:** Grouping results does not imply a combined valid eligibility decision. PMSBY's FAQ and Rules PDF are kept with reconciliation warnings.

**Likely follow-up:** Who resolves contradictory conditions?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q50. What government coverage is verified?

**Simple answer:** Three schemes and four partial reviewed sources.

**Technical answer:** PM-KISAN, PMSBY and Kalyana Lakshmi appear in the coverage report. The Rules PDF supports the PMSBY enrolment/auto-debit form item, not a complete catalogue.

**Likely follow-up:** Why preserve unknown fields?

**Implementation:** [docs/SOURCE_COVERAGE.json](../docs/SOURCE_COVERAGE.json)


## Models and grounded answers

### Q51. What are the Scheme Matcher nodes?

**Simple answer:** A finite sequence from parsing to checked results.

**Technical answer:** parse_request, identify_missing, retrieve, evaluate_rules, rank, explain, validate_citations and return_results form the graph. The trace is diagnostic, not arbitrary tool access.

**Likely follow-up:** Where can a model influence output?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q52. Why deterministic eligibility checks?

**Simple answer:** A model must not invent benefit rules.

**Technical answer:** Typed curated comparisons use documented fields/operators and supporting quotations. A missing value remains unknown; complete local checks still do not grant official approval.

**Likely follow-up:** How would a new condition be added safely?

**Implementation:** [backend/app/ai/models.py](../backend/app/ai/models.py)

### Q53. What if the LLM is unavailable?

**Simple answer:** Preserve bounded evidence-only behavior when possible.

**Technical answer:** Provider failures produce warnings/fallback. No relevant retrieval evidence still means cannot verify, not a model-generated guess. The demonstrated configuration is LLM_PROVIDER=none.

**Project example:** The demonstrated mode sets LLM_PROVIDER=none and still returns citations.

**Likely follow-up:** What if Chroma is unavailable too?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)

### Q54. How are hosted calls controlled?

**Simple answer:** They require explicit configuration and approval.

**Technical answer:** Hosted enablement defaults false; URL/credential/output/time bounds are checked. Recorded verification made no paid inference call.

**Likely follow-up:** What data would leave the machine if enabled?

**Implementation:** [backend/app/ai/providers.py](../backend/app/ai/providers.py)

### Q55. How are token use and cost reported?

**Simple answer:** Use provider metadata and preserve unknowns.

**Technical answer:** Context-local usage records sanitize reported counts. Cost is null when unknown. A successful mock validates transport/accounting behavior, not live model availability.

**Likely follow-up:** Why avoid estimating counts as actual billing?

**Implementation:** [backend/app/ai/providers.py](../backend/app/ai/providers.py)

### Q56. How do you defend against prompt injection?

**Simple answer:** Untrusted text cannot grant new authority.

**Technical answer:** Fixed intents/tools, strict schemas, URL restrictions and citation checks bound execution. A source saying ignore rules cannot create a calendar reservation.

**Likely follow-up:** What risks remain despite these controls?

**Implementation:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py)

### Q57. What conversation memory is stored?

**Simple answer:** A minimal profile and earlier scheme IDs.

**Technical answer:** MatcherService keeps expiring session-owned context and explicit corrections, not raw chat logs. Previous scheme IDs improve follow-up retrieval without an open-ended transcript.

**Likely follow-up:** How is memory bound to a login?

**Implementation:** [backend/app/ai/service.py](../backend/app/ai/service.py)

### Q58. Does Hindi UI imply Hindi RAG quality?

**Simple answer:** No; localization and retrieval evaluation differ.

**Technical answer:** Static dictionaries are measured. The narrow English parser and English MiniLM do not establish Hindi/Telugu free-text retrieval quality.

**Likely follow-up:** How would you evaluate multilingual retrieval?

**Implementation:** [frontend/src/language.tsx](../frontend/src/language.tsx)

### Q59. RAG versus fine-tuning?

**Simple answer:** RAG looks up evidence; fine-tuning changes weights.

**Technical answer:** This project ingests sources and embeds chunks without training a foundation model. Updating official content calls for review/re-ingestion rather than weight training.

**Project example:** A reviewed source update is re-ingested rather than fine-tuning model weights.

**Likely follow-up:** Could both techniques coexist?

**Implementation:** [backend/app/ai/ingestion.py](../backend/app/ai/ingestion.py)

### Q60. Can RAG guarantee correctness?

**Simple answer:** No; grounding reduces some unsupported claims.

**Technical answer:** Retrieval gaps, stale/partial sources and real-world context can still invalidate advice. The matcher must express uncertainty instead of promising benefit approval.

**Likely follow-up:** What evaluation dataset would you create?

**Implementation:** [backend/app/agents/scheme_matcher.py](../backend/app/agents/scheme_matcher.py)


## LangGraph and controlled agents

### Q61. What is LangGraph?

**Simple answer:** A framework for explicit stateful workflow steps.

**Technical answer:** StateGraph connects named callables, typed state and routing. CaseOrchestrator routes document questions through authorized context rather than a single unconstrained prompt.

**Likely follow-up:** Why not just a chain of functions?

**Implementation:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py)

### Q62. What are nodes and edges?

**Simple answer:** Nodes do work and edges connect execution.

**Technical answer:** A callable updates graph state; normal/conditional edges determine the next step. load_context precedes domain tasks and all paths converge on validation/response.

**Likely follow-up:** Which edge is conditional here?

**Implementation:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py)

### Q63. What is graph state?

**Simple answer:** The current request's shared working context.

**Technical answer:** TypedDict fields hold actor, IDs, authorized case, intent, results and trace. This runtime object is not automatically a durable record.

**Likely follow-up:** Where does durable state actually live?

**Implementation:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py)

### Q64. How is intent selected?

**Simple answer:** An explicit enum or narrow keyword routing.

**Technical answer:** identify_intent chooses one fixed task. No generative planner selects arbitrary functions. A wrong auto classification can be corrected with an explicit supported intent.

**Likely follow-up:** How would you test ambiguous wording?

**Implementation:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py)

### Q65. Why five assistance capabilities?

**Simple answer:** The tasks have different evidence and action boundaries.

**Technical answer:** Matching, checklist assessment, reminders, referral and visits are separated so a text response cannot stand in for authorization or scheduling integrity.

**Project example:** A document question routes to DocumentVerifier; a visit question uses DoorstepCoordinator.

**Likely follow-up:** What maintenance overhead does this introduce?

**Implementation:** [backend/app/agents/case_agents.py](../backend/app/agents/case_agents.py)

### Q66. Are all five autonomous AI agents?

**Simple answer:** No; explain them as controlled capabilities.

**Technical answer:** Document/Follow-up/Escalation are deterministic case nodes. Matcher and Doorstep have bounded graphs with optional model-related behavior. DocumentVerifier.analyze uses no LLM.

**Likely follow-up:** What definition of agent are you using?

**Implementation:** [backend/app/agents/case_agents.py](../backend/app/agents/case_agents.py)

### Q67. How do agent handoffs share context?

**Simple answer:** Through fixed interfaces after actor authorization.

**Technical answer:** The orchestrator loads an authorized case. Doorstep context verifies linked-case ownership, and its service governs data visibility. A visit assignment does not grant full case access.

**Likely follow-up:** What can be persisted by a read-only query?

**Implementation:** [backend/app/agents/doorstep_coordinator.py](../backend/app/agents/doorstep_coordinator.py)

### Q68. Are LangGraph checkpoints persisted?

**Simple answer:** No checkpointer is configured in these graphs.

**Technical answer:** graph.compile() has no durable saver. Cases, visits, receipts/jobs and minimal matcher context survive separately; raw prompt/transcript checkpoints are not stored.

**Project example:** graph.compile() has no checkpointer argument; Mongo records provide durability.

**Likely follow-up:** What privacy work would a checkpointer require?

**Implementation:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py)

### Q69. How is human-in-the-loop enforced?

**Simple answer:** The backend requires an authorized confirmed action.

**Technical answer:** Current role, revision, consent and confirmation guard assignment. A model saying approved is not sufficient. Worker acceptance follows coordinator proposal.

**Likely follow-up:** Is this an interrupt-based approval inbox?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)

### Q70. How do graphs terminate?

**Simple answer:** Finite routes end explicitly, with bounded work.

**Technical answer:** START/END edges, supported intent branches, model timeouts and output limits prevent open-ended tool loops. Safe retries reload authoritative domain state.

**Likely follow-up:** What happens on a timeout after mutation?

**Implementation:** [backend/app/agents/doorstep_coordinator.py](../backend/app/agents/doorstep_coordinator.py)


## Case assistance

### Q71. What does the Document Verifier verify?

**Simple answer:** Technical assistance completeness, not legal identity.

**Technical answer:** It evaluates checklist items against unexpired uploaded review states. Missing/unreadable items yield next steps; a ready checklist still does not mean government approval.

**Likely follow-up:** Why avoid calling this KYC?

**Implementation:** [backend/app/agents/case_agents.py](../backend/app/agents/case_agents.py)

### Q72. How is readability checked?

**Simple answer:** Supported file formats receive technical checks.

**Technical answer:** Storage validates signatures/byte limits and PDF/image properties. Uncertain content routes to human review; readability does not prove authenticity or malware safety.

**Likely follow-up:** What extra production file scanning is needed?

**Implementation:** [backend/app/cases/storage.py](../backend/app/cases/storage.py)

### Q73. Is OCR always available?

**Simple answer:** No; it is optional and environment-dependent.

**Technical answer:** The OCR setting gates a Tesseract-dependent path. When unavailable, the application preserves review/fallback rather than inventing extracted text.

**Likely follow-up:** How would you validate OCR accuracy?

**Implementation:** [backend/app/cases/storage.py](../backend/app/cases/storage.py)

### Q74. Who accepts a checklist document?

**Simple answer:** An authorized human reviewer.

**Technical answer:** The service records reviewer/time/note and requires a verified source checklist for acceptance. A successful review can change assistance readiness, not legal validity.

**Likely follow-up:** What happens when a document expires?

**Implementation:** [backend/app/cases/service.py](../backend/app/cases/service.py)

### Q75. Who can download a private file?

**Simple answer:** An authorized actor through the API.

**Technical answer:** The service checks case access before returning bytes. Expired/deleted/removed files fail even if a caller knows a record ID.

**Likely follow-up:** How is the file storage key protected?

**Implementation:** [backend/app/cases/api.py](../backend/app/cases/api.py)

### Q76. What makes follow-ups durable?

**Simple answer:** The due time and delivery state are in Mongo.

**Technical answer:** A separate worker polls schedules and writes reminders with guarded revisions. Browser reload or an application restart cannot erase the schedule.

**Likely follow-up:** When do overdue jobs resume after downtime?

**Implementation:** [backend/app/cases/worker.py](../backend/app/cases/worker.py)

### Q77. How do quiet hours work?

**Simple answer:** Notifications wait until the allowed local time.

**Technical answer:** FollowUpAgent.next_allowed uses Asia/Kolkata quiet windows and frequency. Equal start/end disables the quiet period. Quiet-hour behavior is not browser-clock scheduling.

**Likely follow-up:** What would multi-timezone support change?

**Implementation:** [backend/app/agents/case_agents.py](../backend/app/agents/case_agents.py)

### Q78. How are duplicate reminders prevented?

**Simple answer:** Persistent identities and guarded writes decide delivery.

**Technical answer:** A reminder references its follow-up ID, and CAS rejects competing stale saves. Retry processing is distinct from falsely promising exactly-once external transport.

**Likely follow-up:** What does at-least-once processing mean?

**Implementation:** [backend/app/cases/automation.py](../backend/app/cases/automation.py)

### Q79. What triggers escalation?

**Simple answer:** Explicit help or unresolved configured conditions.

**Technical answer:** Rules check inactivity, repeated missing documents, delayed reviews and conflict flags. This creates an internal coordinator referral, not a department complaint.

**Likely follow-up:** Which trigger is high severity?

**Implementation:** [backend/app/agents/case_agents.py](../backend/app/agents/case_agents.py)

### Q80. How is escalation resolved?

**Simple answer:** A coordinator acknowledges or resolves it with a note.

**Technical answer:** Status, owner, timestamps, reopening rules and activity persist. Resolving all referrals can resume the saved assistance stage.

**Likely follow-up:** Which closed-case changes are forbidden?

**Implementation:** [backend/app/cases/service.py](../backend/app/cases/service.py)


## SevaSetu and integrity

### Q81. What makes a worker eligible?

**Simple answer:** Account, verification, scope and calendar must fit.

**Technical answer:** The service checks current role/active state, expiry through visit end, category/language/area/capabilities, organization, capacity and overlap. A free slot alone is insufficient.

**Likely follow-up:** Why recheck during assignment?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)

### Q82. How are candidates ranked?

**Simple answer:** Lower workload first, then stable worker ID.

**Technical answer:** The deterministic order is inspectable. Choosing a lower-ranked eligible worker needs an override reason. This is not a trained recommendation model.

**Likely follow-up:** What fairness concerns remain?

**Implementation:** [backend/app/agents/doorstep_coordinator.py](../backend/app/agents/doorstep_coordinator.py)

### Q83. How is geographic matching done?

**Simple answer:** Declared coverage is compared with the request.

**Technical answer:** Case-insensitive district matching and optional mandal/village areas implement scope. There is no nearest-worker route optimization or automatic travel-time estimate.

**Likely follow-up:** Why not claim GPS routing?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)

### Q84. How do you prevent double bookings?

**Simple answer:** One calendar document is the atomic conflict authority.

**Technical answer:** SevaStore.reserve filters revision, current verification, capacity and overlapping reservations in one update. Competing overlapping writes cannot both win that authority.

**Project example:** Two overlapping reservations compete on one worker revision.

**Likely follow-up:** What race should integration tests exercise?

**Implementation:** [backend/app/seva/store.py](../backend/app/seva/store.py)

### Q85. What is compare-and-swap?

**Simple answer:** Save only if the version still matches your read.

**Technical answer:** Updates/replacements include revision in the filter. A stale operation returns409. This prevents a later stale form from silently erasing another actor's work.

**Likely follow-up:** Is a prior read alone sufficient?

**Implementation:** [backend/app/cases/store.py](../backend/app/cases/store.py)

### Q86. What is idempotency?

**Simple answer:** A repeated intended action must not repeat its effect.

**Technical answer:** Operation keys and payload fingerprints distinguish valid replay from reuse with changed details. Creation uses unique owner/key authority rather than disabling a button.

**Project example:** Replaying the same creation key/payload returns the existing owned creation.

**Likely follow-up:** How is this different from concurrency control?

**Implementation:** [backend/app/cases/service.py](../backend/app/cases/service.py)

### Q87. Are all multi-document actions transactional?

**Simple answer:** No; recovery is deliberately conservative on standalone Mongo.

**Technical answer:** Reservation, booking save and release have guarded/compensating behavior. Do not claim universal distributed atomicity or perfect failure recovery.

**Likely follow-up:** What could replica-set transactions improve?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)

### Q88. What does rescheduling change?

**Simple answer:** It proposes a new window and requires acceptance again.

**Technical answer:** Pre-outcome active requests release the old assignment/calendar commitment. Started/performed outcomes use problem reporting/follow-up rather than ordinary cancellation.

**Likely follow-up:** Why not silently reuse the worker?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)

### Q89. How are missed visits handled?

**Simple answer:** Overdue unstarted appointments trigger internal review.

**Technical answer:** Automation records no-show/missed state, releases reservation and creates notice/escalation reasons. Repeated misses can raise severity.

**Likely follow-up:** Can an unstarted visit be completed?

**Implementation:** [backend/app/seva/automation.py](../backend/app/seva/automation.py)

### Q90. Who confirms completion and feedback?

**Simple answer:** Worker submits services; coordinator reviews; citizen can rate.

**Technical answer:** Outcome submission and reviewed completion are different stages. A retry-safe outbox appends completion activity to a linked case. The demo outcome is explicitly simulated.

**Likely follow-up:** Does completion imply a government benefit?

**Implementation:** [backend/app/seva/service.py](../backend/app/seva/service.py)


## Security and experience

### Q91. Authentication versus authorization?

**Simple answer:** Identity and permission are different checks.

**Technical answer:** A valid opaque session resolves an active actor; role and object checks still apply. A logged-in citizen cannot read admin users.

**Likely follow-up:** Can a valid token read any case?

**Implementation:** [backend/app/auth.py](../backend/app/auth.py)

### Q92. Do you use JWT?

**Simple answer:** No; these are opaque bearer sessions.

**Technical answer:** Random tokens are hashed server-side and checked against expiry/current user/auth_version. Logout revokes the session; account changes invalidate old versions.

**Project example:** Logout removes a server-side hashed opaque session.

**Likely follow-up:** Why choose server-side revocation?

**Implementation:** [backend/app/auth.py](../backend/app/auth.py)

### Q93. How are passwords stored?

**Simple answer:** Salted scrypt hashes, not plaintext.

**Technical answer:** Explicit scrypt parameters and constant-time comparison protect verification. Password spaces are preserved; a regression guards against accidental trimming.

**Likely follow-up:** What recovery and MFA remain absent?

**Implementation:** [backend/app/auth.py](../backend/app/auth.py)

### Q94. What does RBAC protect?

**Simple answer:** Roles restrict classes of operations.

**Technical answer:** Citizen, worker, coordinator and admin have different capabilities. Public signup cannot set a role, and existing admins cannot be removed through the user-management API.

**Likely follow-up:** Why also check ownership?

**Implementation:** [backend/app/admin.py](../backend/app/admin.py)

### Q95. How is citizen data isolated?

**Simple answer:** Every relevant object check uses the current actor.

**Technical answer:** CaseStore filters owner/coordinator/worker assignment. Visit consent/acceptance controls exact location separately. An unpredictable reference is not sufficient authorization.

**Likely follow-up:** Why return404 for an unowned case?

**Implementation:** [backend/app/cases/store.py](../backend/app/cases/store.py)

### Q96. Can demo accounts enter production?

**Simple answer:** Seeded demo_only accounts are rejected outside development.

**Technical answer:** Both password login and existing-session checks enforce the guard. The demo also has separate Mongo/files/vectors and locally encrypted random passwords.

**Likely follow-up:** Why are both safeguards needed?

**Implementation:** [backend/tests/test_phase5_accounts.py](../backend/tests/test_phase5_accounts.py)

### Q97. What voice support is actually verified?

**Simple answer:** Consent, controls and fallback, not physical speech.

**Technical answer:** Browser recognition/playback depends on supported APIs, installed voices and explicit external-processing consent. en-IN/hi-IN/te-IN settings are not proof of device-language performance.

**Likely follow-up:** What hardware matrix needs testing?

**Implementation:** [frontend/src/voice.tsx](../frontend/src/voice.tsx)

### Q98. What messaging is live?

**Simple answer:** Durable in-app updates; external adapters are unconfigured.

**Technical answer:** Twilio/Meta payloads are mock-tested and require approval/consent/credentials. Provider acceptance is not delivery, and timeout ambiguity must not cause blind paid retries.

**Likely follow-up:** What delivery callback work is missing?

**Implementation:** [backend/app/seva/messaging.py](../backend/app/seva/messaging.py)

### Q99. Why is CI red with passing tests?

**Simple answer:** The dependency audit is an independent release gate.

**Technical answer:** Chroma1.5.9 remains flagged. Embedded fixed-model use narrows exposure but does not patch the package. The backend job stops at OSV after passing its tests/checks.

**Project example:** Linux tests pass, then OSV fails for Chroma rather than being suppressed.

**Likely follow-up:** What would permit public backend release?

**Implementation:** [docs/SECURITY_ADVISORIES.json](../docs/SECURITY_ADVISORIES.json)

### Q100. What is actually deployed?

**Simple answer:** A static interview showcase, with the full platform local.

**Technical answer:** GitHub Pages serves screenshots/docs, not FastAPI/Mongo/Chroma/worker. It collects no credentials and makes no application API requests.

**Likely follow-up:** Why not point public JavaScript at localhost?

**Implementation:** [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)


## Operations, testing and reflection

### Q101. Why use Docker?

**Simple answer:** It packages runtime dependencies and boundaries reproducibly.

**Technical answer:** Separate images/volumes define frontend, backend, Mongo and worker. Remote smoke verifies the rehearsal, not production certification or full fresh-source RAG.

**Likely follow-up:** How does a container differ from a VM?

**Implementation:** [compose.yaml](../compose.yaml)

### Q102. What does Compose orchestrate?

**Simple answer:** Four local services, volumes and health dependencies.

**Technical answer:** Only the frontend port is published to loopback. Mongo has no host port; local unauthenticated Mongo must not be reused unchanged for public production.

**Likely follow-up:** Why must private files/vectors persist?

**Implementation:** [compose.yaml](../compose.yaml)

### Q103. What does Git history preserve?

**Simple answer:** Incremental changes and verified checkpoints.

**Technical answer:** Phase/pause/resume commits explain genuine development progress. The proxy recovery fix followed a failed container smoke test without rewriting history.

**Likely follow-up:** Commit versus push?

**Implementation:** [docs/FINAL_RELEASE_REPORT.md](../docs/FINAL_RELEASE_REPORT.md)

### Q104. What is GitHub's role?

**Simple answer:** Source/history hosting, automation and a static showcase.

**Technical answer:** The authorized public main branch and Pages /docs publication are distinct from runtime backend hosting. Public source visibility is not an open-source license grant.

**Likely follow-up:** Who chooses a license?

**Implementation:** [README.md](../README.md)

### Q105. CI versus CD?

**Simple answer:** CI checks changes; deployment publishes an artifact.

**Technical answer:** Actions runs tests/lint/build/audit/container smoke. Pages publishes static documentation. A failed advisory check is not silently converted to full backend deployment approval.

**Likely follow-up:** Which results are actually green?

**Implementation:** [.github/workflows/ci.yml](../.github/workflows/ci.yml)

### Q106. Unit, integration and end-to-end tests?

**Simple answer:** They exercise different boundaries.

**Technical answer:** Logic tests isolate functions; real-Mongo tests validate persistence/concurrency; Chrome tests use actual UI/API flows. Calendar races need more than a mocked React event.

**Likely follow-up:** Why not rely on one test type?

**Implementation:** [backend/tests/test_seva.py](../backend/tests/test_seva.py)

### Q107. Why use mocks?

**Simple answer:** To test contracts/failures without hardware or paid sends.

**Technical answer:** Voice and provider transport mocks verify local behavior, but cannot prove microphone support, live inference or real delivery. Claims must state that distinction.

**Likely follow-up:** Which integrations need real environment tests?

**Implementation:** [backend/tests/test_phase5_messaging.py](../backend/tests/test_phase5_messaging.py)

### Q108. Why is genuinely free hosting difficult?

**Simple answer:** The stack needs persistent native storage and an always-running worker.

**Technical answer:** Reviewed no-card INR 0 tiers have sleep/disk/worker/card limits. A static showcase is honest; a fake backend or silently removed features would not satisfy the architecture.

**Likely follow-up:** What does reliable self-hosting require?

**Implementation:** [docs/FREE_HOSTING_REVIEW.md](../docs/FREE_HOSTING_REVIEW.md)

### Q109. How would you scale to a million users?

**Simple answer:** Measure bottlenecks before proposing a redesign.

**Technical answer:** Partition operations, bound audit growth, use private object storage, assess queued jobs/replica-set integrity and evaluate retrieval. These are future proposals, not measured current capacity.

**Project example:** Current caps and embedded storage are not million-user scale evidence.

**Likely follow-up:** Which measurement comes first?

**Implementation:** [docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md)

### Q110. What would you improve next?

**Simple answer:** Resolve release gates and evaluate real use before claiming maturity.

**Technical answer:** Prioritize dependency remediation/review, recovery/MFA, native language/speech evaluation and a complete quiesced restore drill. Describe personal learning in your own words.

**Likely follow-up:** Which improvement can you implement and defend?

**Implementation:** [docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md)


## Honest reflection and ownership

For "what did you personally learn?", describe something you actually practiced: trace a request,
draw an overlapping-slot race, explain why partial evidence stays unknown, or demonstrate a denied
cross-account call. Suggested lessons are prompts for reflection, not a verified personal biography.
For "did you write every line?", explain AI coding assistance, your review/test decisions and which
implementation you can now explain independently. Never claim real users, production deployment,
live models or accuracy percentages without evidence. [Portfolio wording](PORTFOLIO_GUIDE.md).
