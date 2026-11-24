# Project walkthrough: a beginner-to-intermediate mini-course

Read one chapter with the source file open. Excerpts are exact fragments from this checkout, sometimes incomplete by design; surrounding code is available through the link. Historical test results are dated in [the release report](FINAL_RELEASE_REPORT.md). No live model, native speech or full hosted backend is implied.

Start with [the glossary](GLOSSARY.md) whenever a word is unfamiliar. Comparative technology reasons below are retrospective unless a historical record states otherwise.

## Chapter 1: Understanding the problem

**Beginner explanation:** A scheme answer is only one step toward useful assistance.

**Analogy:** A library desk can find a book, but a support desk helps the visitor complete the next task.

**Technical implementation:** YojanaSetu links discovery/evidence to private cases. SevaSetu links those cases to consented visits. Intended accessibility/social value is not measured adoption.

**Read:** [backend/app/models.py](../backend/app/models.py#L51)

```python
class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    scheme_id: str = Field(min_length=1, max_length=80)
    assistance_type: str = Field(min_length=3, max_length=120)
```

**Reading the excerpt:** The request identifies a scheme and an assistance need without demanding government identity data.

**Remember:** Describe intended users without inventing impact statistics.

**Self-assessment:** What can a citizen do after receiving an uncertain answer? Also trace the next caller or persisted field in the source before moving on.

## Chapter 2: How full-stack applications work

**Beginner explanation:** The browser and server have separate responsibilities.

**Analogy:** A restaurant menu presents choices; the kitchen validates and fulfills an order.

**Technical implementation:** React handles interaction, FastAPI validates and authorizes HTTP, and Mongo stores operational truth. A button's visual state is not proof of a database mutation.

**Read:** [frontend/src/auth.tsx](../frontend/src/auth.tsx#L18)

```tsx
  const response = await fetch(`${base}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined
        ? {}
        : { 'Content-Type': 'application/json', 'Idempotency-Key': key || crypto.randomUUID() }),
    },
```

**Reading the excerpt:** The fetch URL targets the API, the method depends on a body, and the bearer header identifies the session.

**Remember:** Trace a click through a response and stored record.

**Self-assessment:** Where would you inspect a request that returns409? Also trace the next caller or persisted field in the source before moving on.

## Chapter 3: React frontend

**Beginner explanation:** A component turns state into an interface.

**Analogy:** Reusable counters at a service centre share signs but handle different queues.

**Technical implementation:** main.tsx defines routes; auth/language contexts provide shared state. private-cases.tsx and seva.tsx hold domain screens. Hooks manage loading and errors without introducing Redux.

**Read:** [frontend/src/auth.tsx](../frontend/src/auth.tsx#L88)

```tsx
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
```

**Reading the excerpt:** State setters update the controlled form; they do not authenticate the user by themselves.

**Remember:** Understand component state versus server authority.

**Self-assessment:** What happens to memory-only auth after reload? Also trace the next caller or persisted field in the source before moving on.

## Chapter 4: FastAPI backend

**Beginner explanation:** Routes translate HTTP requests into domain calls.

**Analogy:** A receptionist checks the form before sending it to the responsible team.

**Technical implementation:** main.py composes routers and dependencies. Services enforce allowed actions. Response models and safe errors reduce accidental leakage. OpenAPI describes the current contract.

**Read:** [backend/app/main.py](../backend/app/main.py#L48)

```python
    app = FastAPI(title="YojanaSetu + SevaSetu · Phase 5 RC", lifespan=lifespan)
    app.state.ai_service = ai_service
    app.state.settings = settings
    app.state.private_runtime = private_runtime
    app.state.private_initialization_lock = asyncio.Lock()
```

**Reading the excerpt:** The application is constructed, receives settings/runtime references and later installs routers and guards.

**Remember:** Find the app entry point before reading individual endpoints.

**Self-assessment:** Where does a route get its current actor? Also trace the next caller or persisted field in the source before moving on.

## Chapter 5: APIs and HTTP

**Beginner explanation:** Methods and status codes describe operations and outcomes.

**Analogy:** A numbered request slip specifies what work is being requested.

**Technical implementation:** GET reads resources. POST creates or performs explicit guarded actions. The implementation has no PUT/PATCH routes; No DELETE endpoint is exposed either; private document deletion uses a guarded POST action. Revision conflicts differ from invalid input.

**Read:** [frontend/src/auth.tsx](../frontend/src/auth.tsx#L19)

```tsx
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined
        ? {}
        : { 'Content-Type': 'application/json', 'Idempotency-Key': key || crypto.randomUUID() }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
```

**Reading the excerpt:** The method chooses read or mutation, headers carry authorization and a key, and JSON serializes the request body.

**Remember:** A network response must be checked before trusting its content.

**Self-assessment:** Why is a409 different from a401? Also trace the next caller or persisted field in the source before moving on.

## Chapter 6: MongoDB

**Beginner explanation:** Documents hold operational data and nested state.

**Analogy:** An assistance folder contains its checklist, notes, receipts and reminders.

**Technical implementation:** assistance_cases embeds related arrays; users/sessions and seva calendars are separate collections. Indexes support lookup/uniqueness. This is an observed model, not a universal claim that NoSQL is superior.

**Read:** [backend/app/cases/store.py](../backend/app/cases/store.py#L19)

```python
def actor_filter(actor):
    if actor.role == UserRole.admin:
        return {}
    if actor.role == UserRole.citizen:
        return {"owner_id": actor.id}
    if actor.role == UserRole.coordinator:
        return {"coordinator_id": actor.id}
    return {"worker_ids": actor.id}

```

**Reading the excerpt:** The role selects an exact filter; citizen ownership, coordinator responsibility and worker case assignment are different relations.

**Remember:** Operational permissions come from exact data, not similarity search.

**Self-assessment:** Which indexes support replay-safe case creation? Also trace the next caller or persisted field in the source before moving on.

## Chapter 7: Authentication and security

**Beginner explanation:** Identity and permission are different checks.

**Analogy:** A staff badge identifies a person, but does not open every cabinet.

**Technical implementation:** Opaque bearer sessions are hashed in Mongo, expire and can be revoked. Current user role/active/auth_version is rechecked. Object ownership is required after login. Public signup cannot request staff authority.

**Read:** [backend/app/auth.py](../backend/app/auth.py#L62)

```python
async def current_actor(request: Request, authorization: str = Header(default="")) -> Actor:
    if not authorization.startswith("Bearer ") or len(authorization) > 200:
        raise HTTPException(401, "Sign in to access private assistance cases.")
    runtime = await private_runtime(request)
    session = await runtime.auth.session(token_hash(authorization[7:]))
    if not session:
        raise HTTPException(401, "Session expired or revoked. Sign in again.")
```

**Reading the excerpt:** The header format is checked, the token is hashed for lookup and an absent session fails before domain access.

**Remember:** This project does not use JWT; a hidden UI control is not authorization.

**Self-assessment:** How does a worker visit assignment differ from case access? Also trace the next caller or persisted field in the source before moving on.

## Chapter 8: Artificial intelligence and LLMs

**Beginner explanation:** A language model can help explain text, but cannot establish permission or official facts.

**Analogy:** A writing assistant can draft an explanation while the evidence and approval remain with people.

**Technical implementation:** LanguageModel supports optional local/approved hosted transports with bounded calls. The verified demo uses LLM_PROVIDER=none. Mocked protocol tests are not a successful real inference call.

**Read:** [backend/app/config.py](../backend/app/config.py#L21)

```python
    llm_provider: Literal["none", "ollama", "openai_compatible"] = "none"
    llm_model: str = "qwen2.5:3b"
    model_base_url: str = "http://127.0.0.1:11434"
    model_api_key: str = ""
```

**Reading the excerpt:** The default provider is none; model name/base URL are configuration, not proof that a server is running.

**Remember:** Separate configured, mock-tested and live-verified behavior.

**Self-assessment:** What happens when the model cannot be reached? Also trace the next caller or persisted field in the source before moving on.

## Chapter 9: Embeddings and vector databases

**Beginner explanation:** Embeddings make text comparable as numeric vectors.

**Analogy:** A library can group related subjects even when their titles use different words.

**Technical implementation:** The ONNX MiniLM provider embeds query and source text. Chroma persists cosine-searchable public chunks. Collection embedding identity prevents accidentally mixing incompatible models. Similarity does not guarantee relevance or truth.

**Read:** [backend/app/ai/vectors.py](../backend/app/ai/vectors.py#L13)

```python
        self.client = chromadb.PersistentClient(
            path=path, settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name,
            embedding_function=None,
            metadata={"embedding_identity": embeddings.identity, "hnsw:space": "cosine"},
        )
```

**Reading the excerpt:** The embedded client opens persistent storage, then retrieves/creates a named collection with explicit embedding handling.

**Remember:** Mongo handles exact records; Chroma searches public text.

**Self-assessment:** Why must a model change trigger re-ingestion? Also trace the next caller or persisted field in the source before moving on.

## Chapter 10: RAG

**Beginner explanation:** Retrieve evidence before giving grounded guidance.

**Analogy:** An open-book examination requires finding and citing the relevant passage.

**Technical implementation:** The operator admits reviewed sources, extracts text, chunks it, hashes/versions metadata and embeds it. Query retrieval is filtered to active verified evidence before curated rule checks and citation validation.

**Read:** [backend/app/ai/ingestion.py](../backend/app/ai/ingestion.py#L105)

```python
def chunk_document(
    pages, manifest: SourceManifest, content_hash: str, version: str, size=1100, overlap=200
) -> list[Chunk]:
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed nonnegative overlap")
```

**Reading the excerpt:** Chunking receives reviewed metadata plus content/version identity, then uses bounded overlapping character windows.

**Remember:** RAG is a workflow for evidence, not a guarantee of eligibility.

**Self-assessment:** Why can PMSBY remain unknown despite a relevant passage? Also trace the next caller or persisted field in the source before moving on.

## Chapter 11: LangGraph

**Beginner explanation:** A graph makes processing order and branching explicit.

**Analogy:** A flowchart tells staff which desk comes next and when the work ends.

**Technical implementation:** StateGraph attaches names to functions and adds normal/conditional edges. CaseGraphState carries the actor and authorized case. No persisted graph checkpointer is configured; domain state is durable separately.

**Read:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py#L47)

```python
        graph.add_edge(START, "identify_intent")
        graph.add_edge("identify_intent", "load_context")
        graph.add_conditional_edges(
            "load_context",
            lambda s: s["intent"],
            {
                name: name
                for name in (
```

**Reading the excerpt:** START selects the first step; context loads next; conditional routing selects a supported intent branch.

**Remember:** Graph state and database state have different lifetimes.

**Self-assessment:** Where do paths converge before responding? Also trace the next caller or persisted field in the source before moving on.

## Chapter 12: Five-agent architecture

**Beginner explanation:** Five capabilities have distinct evidence and authority boundaries.

**Analogy:** A support team has a reference librarian, checklist reviewer, reminder clerk, referral desk and visit planner.

**Technical implementation:** Matcher and Doorstep have bounded graphs. Document/Follow-up/Escalation are deterministic nodes within CaseOrchestrator, not three separate LLMs. Fixed handoffs reuse guarded services.

**Read:** [backend/app/agents/case_orchestrator.py](../backend/app/agents/case_orchestrator.py#L99)

```python
    async def documents(self, state):
        return self.step(
            state, "document_verifier", result=DocumentVerifier().analyze(state["case"], now_utc())
        )

```

**Reading the excerpt:** The branch calls DocumentVerifier on the already authorized case and records a diagnostic trace label.

**Remember:** Explain controlled agent behavior without exaggerating autonomy.

**Self-assessment:** What prevents an agent from assigning itself new permissions? Also trace the next caller or persisted field in the source before moving on.

## Chapter 13: Case assistance

**Beginner explanation:** A private case preserves progress and accountable human intervention.

**Analogy:** A folder is passed between authorized desks, with every change recorded.

**Technical implementation:** Cases contain source checklist versions, upload metadata, review states, reminders, referrals and activity. Mutation checks revision and idempotency before storing the winning result. Human checklist review is not legal identity verification.

**Read:** [backend/app/cases/service.py](../backend/app/cases/service.py#L171)

```python
    async def mutate(self, case_id, actor, revision, key, action, payload, change):
        case = await self.authorized(case_id, actor)
        hashed, digest = operation_key(key), fingerprint(payload)
        existing = next((o for o in case.operations if o["key"] == hashed), None)
        if existing:
            if existing["action"] != action or existing["fingerprint"] != digest:
                raise HTTPException(409, "Idempotency key was reused for a different action.")
            return case
        if case.revision != revision:
```

**Reading the excerpt:** The service authorizes, fingerprints the action, detects valid replay and rejects a stale revision.

**Remember:** A retry and a competing update are different problems.

**Self-assessment:** Which data must remain private during document review? Also trace the next caller or persisted field in the source before moving on.

## Chapter 14: SevaSetu coordination

**Beginner explanation:** A visit is a lifecycle, not a chat promise.

**Analogy:** Booking a support appointment needs consent, a qualified person and a free calendar slot.

**Technical implementation:** The service checks current account/verification, category, language, area, accessibility, organization, capacity and overlap. A single worker document is the atomic reservation authority; human approval and worker acceptance remain separate.

**Read:** [backend/app/seva/store.py](../backend/app/seva/store.py#L32)

```python
    async def reserve(self, worker, booking_id, window, now, expected_booking_revision):
        # One atomic calendar document is the conflict authority, even on standalone MongoDB.
        query = {
            "id": worker["id"],
            "revision": worker["revision"],
            "active": True,
            "verification_status": {"$in": ["verified_internally", "authorization_confirmed"]},
            "verification_expires_at": {"$gt": window.end},
            "reservations": {
```

**Reading the excerpt:** The atomic filter includes worker identity, revision and eligibility state before considering calendar overlap.

**Remember:** Availability read earlier is not a reservation.

**Self-assessment:** What happens when two coordinators choose overlapping slots? Also trace the next caller or persisted field in the source before moving on.

## Chapter 15: Multilingual and voice features

**Beginner explanation:** Translated controls and spoken input are separate capabilities.

**Analogy:** Changing a form's language does not retrain the person interpreting its content.

**Technical implementation:** Static dictionaries support en/hi/te preferences and locale formatting. Official evidence remains source language. Speech recognition/playback require capability and explicit external-processing consent; native hardware support is unverified.

**Read:** [frontend/src/language.tsx](../frontend/src/language.tsx#L4)

```tsx
export function translate(text: string, language: string): string {
  const result = translations[text.trim()]?.[language as 'hi' | 'te'];
  return language === 'en' || !result
    ? text
    : `${text.startsWith(' ') ? ' ' : ''}${result}${text.endsWith(' ') ? ' ' : ''}`;
}
```

**Reading the excerpt:** The dictionary lookup selects the target language and preserves the original text when a translation is unavailable.

**Remember:** Measured static coverage does not certify translation meaning or multilingual RAG.

**Self-assessment:** How does the application remain usable without a microphone? Also trace the next caller or persisted field in the source before moving on.

## Chapter 16: Testing

**Beginner explanation:** Different tests answer different questions.

**Analogy:** Inspecting a component, running a complete machine and rehearsing a whole service are complementary checks.

**Technical implementation:** Pytest covers logic and real Mongo; Vitest covers UI behavior; Chrome exercises actual screens/API. Provider/voice mocks avoid paid calls or hardware claims. Recorded counts are dated evidence, not coverage percentages.

**Read:** [backend/tests/test_phase5_accounts.py](../backend/tests/test_phase5_accounts.py#L13)

```python
def test_demo_accounts_and_existing_sessions_are_rejected_outside_development(live):
    c, headers, settings = live

    async def mark_demo():
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
```

**Reading the excerpt:** The regression uses the real-Mongo fixture and prepares an explicitly marked demo actor before asserting production rejection.

**Remember:** A green mock is not a live integration.

**Self-assessment:** Which test would catch an overlapping calendar race? Also trace the next caller or persisted field in the source before moving on.

## Chapter 17: Git and GitHub

**Beginner explanation:** Git records changes; GitHub hosts history and automation.

**Analogy:** A versioned notebook lets you explain why the current design exists.

**Technical implementation:** Historical commits preserve foundation, RAG, cases, pause/resume and integration. The release sequence includes a failed restart smoke check followed by the proxy fix. Main was pushed without force and visibility stayed public.

**Read:** [.github/workflows/ci.yml](../.github/workflows/ci.yml#L21)

```yaml
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v6
        with: {python-version: '3.12', cache: pip, cache-dependency-path: backend/requirements.lock.txt}
      - run: python -m pip install -r backend/requirements.lock.txt
```

**Reading the excerpt:** Checkout loads the committed source, then the runtime setup step selects the interpreter used for checks.

**Remember:** A commit, push, CI run and deployment are separate events.

**Self-assessment:** Does public visibility provide a project license? Also trace the next caller or persisted field in the source before moving on.

## Chapter 18: Docker and deployment

**Beginner explanation:** Containers package services but do not supply free persistent hosting automatically.

**Analogy:** Packing tools into labelled boxes does not provide a workshop or durable storage.

**Technical implementation:** Compose defines Mongo, backend, worker and frontend with named volumes/health checks. GitHub Pages publishes only static evidence. Nginx resolves backend service DNS again after replacement; remote smoke checks restart/replacement persistence.

**Read:** [frontend/nginx.conf](../frontend/nginx.conf#L8)

```text
    resolver 127.0.0.11 valid=5s ipv6=off;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy no-referrer always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
```

**Reading the excerpt:** Docker's internal resolver refreshes service-name resolution; subsequent headers preserve browser protections.

**Remember:** A local rehearsal is not a production-certified public backend.

**Self-assessment:** Why would an ephemeral free service lose uploaded files? Also trace the next caller or persisted field in the source before moving on.

## Chapter 19: Complete system walkthrough

**Beginner explanation:** Follow one synthetic case end to end.

**Analogy:** A visitor moves through reference, review, referral and appointment desks with one tracked record.

**Technical implementation:** Start at login, discover PMSBY, inspect grounded citations/unknowns, create a private case, upload a synthetic PDF, review reminders/referral, then create a linked visit. Coordinator approval, worker acceptance/check-in and reviewed outcome precede feedback and case-sync activity.

**Read:** [backend/app/seva/automation.py](../backend/app/seva/automation.py#L18)

```python
async def sync_case(service, booking):
    if not booking.get("case_sync_pending") or not booking["case_id"]:
        return
    key = fingerprint(["seva-completed", booking["id"]])
    event = Event(
        actor_id="system:seva",
        action="doorstep_completion_reviewed",
```

**Reading the excerpt:** The completion sync checks its pending flag and builds a stable operation identity before appending case activity.

**Remember:** A completed internal visit is not an official scheme decision.

**Self-assessment:** Which state is authoritative if the browser is stale? Also trace the next caller or persisted field in the source before moving on.

## Chapter 20: Limitations and future improvements

**Beginner explanation:** A useful prototype must explain its limits.

**Analogy:** A tested practice clinic is not automatically an accredited public service.

**Technical implementation:** Chroma advisories, partial source coverage, draft language review, unverified live models/speech/messaging and full production recovery/scale remain separate gates. Proposed improvements require evidence, not invented accuracy or user counts.

**Read:** [backend/app/config.py](../backend/app/config.py#L30)

```python
    allow_hosted_llm: bool = False
    enable_citizen_registration: bool = True
    ai_timeout_seconds: float = Field(default=90, ge=1, le=600)
    retrieval_top_k: int = Field(default=8, ge=1, le=30)
```

**Reading the excerpt:** Hosted inference defaults off and operational settings are bounded; enabling configuration does not establish verification.

**Remember:** Prioritize dependency/security review and measured evaluation before wider release.

**Self-assessment:** What would you measure before redesigning for scale? Also trace the next caller or persisted field in the source before moving on.

## Technology rationale and alternatives

These explanations describe the current architecture and reasonable retrospective trade-offs. They do not assert undocumented original experiments or performance comparisons.

| Choice | Why it fits this implementation | Reasonable alternative / trade-off |
| --- | --- | --- |
| React/TypeScript | Reusable stateful citizen/staff screens and typed use of response data | Plain JS reduces framework machinery but requires explicit DOM/state discipline; TS still needs runtime validation |
| Vite | Development server and compiled browser assets | Another bundler could work; Vite does not host the backend |
| Tailwind/custom CSS | Utility/base processing plus deliberate application layouts | A component library could reduce custom styling but still needs accessibility review |
| Python/FastAPI/Pydantic | Native AI/PDF libraries and explicit typed request/dependency boundaries | Flask is lighter; Django supplies broader built-in product features; neither is inherently wrong |
| Async PyMongo/Mongo | Nested operational state, atomic per-document guards and TTL/unique indexes | Relational models provide joins/constraints and transactions; current standalone recovery has real limits |
| Chroma/ONNX | Explicit local vectors, cosine search and provider identity | Atlas Vector Search or other stores could simplify deployment, but require evaluation/migration; Chroma's advisory is unresolved |
| LangGraph | Visible finite state transitions and task routing | Direct functions could work for simpler flows; graphs do not create authority automatically |
| Curated rules | Reproducible evidence-backed checks and explicit unknowns | LLM-only eligibility would introduce unsupported decisions |
| RAG | Sources can be reviewed, updated and cited without training model weights | Fine-tuning may change style/behavior but does not replace provenance |
| Opaque sessions | Straightforward server-side expiry/revocation and current-account checks | JWT can reduce some lookups but needs revocation/role-change design; it is not used here |
| Polling worker | Durable schedules without extra queue infrastructure in the local project | Managed queues/workers can improve scale/latency but add operational responsibility |
| Private local files | Simple local demonstration with guarded API access | Production object storage needs encryption, retention, access and backup design |
| Docker/Compose/Nginx | Explicit local service boundaries and reproducible Linux smoke checks | A managed platform still needs persistence, worker support and secret/HTTPS configuration |
| GitHub Actions/Pages | Public-source checks and static interview evidence | Pages cannot execute the application backend; CI failing a security gate is useful evidence |

## Folder map and source reading order

```text
YojanaSetu/
  README.md                         recruiter entry point
  frontend/src/main.tsx             route composition and public screens
  frontend/src/auth.tsx             session context and privateApi
  frontend/src/private-cases.tsx    citizen/coordinator case screens
  frontend/src/seva.tsx              worker/visit/verification screens
  frontend/src/language.tsx         locale/context/dictionary lookup
  frontend/src/voice.tsx             consented browser speech controls
  backend/app/main.py               FastAPI composition and legacy compatibility
  backend/app/auth.py               opaque sessions and current_actor
  backend/app/admin.py              safe account/operations APIs
  backend/app/cases/                 private domain models/service/store/files/jobs
  backend/app/seva/                  visits/workers/calendars/outbox/adapters
  backend/app/agents/                matcher/case/doorstep graphs and rule agents
  backend/app/ai/                    ingestion/providers/vector and knowledge stores
  backend/sources/                  reviewed source manifests, not private uploads
  backend/tests/                    logic and real-Mongo tests
  backend/scripts/                  ingestion verification/demo/container/audit helpers
  frontend/scripts/                 measured localization inventory
  compose.yaml                      local four-service runtime
  .github/workflows/ci.yml           test/build/audit/container checks
  docs/                             current guides and dated historical evidence
  presentations/                    slide sources and verified PDF export
```

Read: models -> auth/current_actor -> one route -> service -> store -> related React caller -> tests -> graphs -> ingestion/vectors/providers -> worker -> deployment. Do not start by memorizing library names. For each layer, ask what data it owns and which checks it cannot delegate.

## Genuine challenges and lessons

| Evidence-backed incident or constraint | Resolution / remaining limit | Learn from |
| --- | --- | --- |
| localhost connection refused after services stop | Start Mongo, backend, worker and frontend; verify actual health rather than assuming a prior session stays alive | LOCAL_SETUP_WINDOWS.md |
| Partial official content and a TLS failure on a www URL | Used an accessible official non-www PDF with valid TLS; did not bypass validation or invent fields | source manifests and RAG_PIPELINE.md |
| Live Ollama unavailable | Verified evidence-only mode and mock provider boundaries; did not claim real model inference | FINAL_RELEASE_REPORT.md |
| Password trimming and stale-login matcher responses | Preserved password whitespace and guarded session-owned results with focused regressions | auth.py and session-results.test.tsx |
| Human assignment returned a stale graph stage | Graph now uses the resulting booking for its response | doorstep_coordinator.py |
| Scheduler raced synthetic fixture setup | Seed fixture data before starting its worker; preserve CAS rather than weakening guards | local_demo.py |
| Backend restart produced a proxy 502 | Docker DNS refresh and bounded proxy-readiness/replacement checks passed remotely | nginx.conf and verify_container_runtime.py |
| Unpatched dependency findings | Kept the CI gate failing and public backend release blocked | SECURITY_ADVISORIES.json |
| Reviewed free hosts lack reliable persistence/worker fit | Published clearly labeled static evidence, retained complete local functionality | FREE_HOSTING_REVIEW.md |

These are documented incidents and constraints, not invented development stories. Future scale, native-language evaluation, account recovery/MFA and production restore work remain proposals. Practice explaining one limitation and one verified fix in your own words.


## Language, voice and messaging: exact operating status

| Capability | Implementation and evidence | Boundary |
| --- | --- | --- |
| Static UI | en plus draft hi/te dictionaries; measured 456/456 captured unique phrases and 534 dictionary entries | This is dictionary coverage, not a native-language quality score |
| Preferences | Device language persists; account language can be saved for later sign-ins; case/visit notices have their own preferences | Official evidence and some diagnostics keep source language |
| Speech input | Browser capability detection, explicit external-processing consent, editable transcript and manual use-as-question | Native microphone accuracy/language support was not tested |
| Spoken response | Opt-in installed matching browser voice, replay/stop and consent withdrawal cleanup | en-IN/hi-IN/te-IN selection is not proof of actual playback on every device |
| In-app notifications | Persisted generic localized case/visit events, quiet hours, frequency, replay and acknowledgements | A new event may wait; a running worker is required |
| External SMS/WhatsApp | Twilio/Meta adapters have contract mocks and approval/consent guards | Unconfigured, not wired to automatic sending; no live delivery or signed callbacks verified |

See [the measured inventory](LOCALIZATION_COVERAGE.json), [voice implementation](../frontend/src/voice.tsx)
and [messaging adapters](../backend/app/seva/messaging.py). No paid send or model call is needed to study
or demonstrate the verified local mode. Fix missing native-language evaluation rather than inventing a score.
