# Technical glossary with project examples

Read a term here, then find its implementation through the [walkthrough](PROJECT_WALKTHROUGH.md) or [source map](ARCHITECTURE.md). Definitions describe this project rather than implying every possible implementation.

| Term | Simple meaning | Example in this repository |
| --- | --- | --- |
| Frontend | The interface running in a browser | React citizen and worker screens |
| Backend | Server-side rules and data access | FastAPI routes and case/Seva services |
| API | An agreed way for software to request work | POST /api/cases |
| REST | A resource-oriented style for HTTP APIs | Scheme/case/visit URLs with explicit methods and status codes |
| HTTP | The request-response protocol | Browser asks FastAPI for JSON |
| GET | Read a representation | GET /api/schemes |
| POST | Create or submit an operation | A confirmed visit assignment |
| PUT / PATCH / DELETE | Common replacement/partial-update/deletion methods | No current routes expose these; private document deletion is a guarded POST action |
| JSON | A structured text data format | scheme_id and assistance_type in a request body |
| Schema | Rules for a data structure | Pydantic BookingInput rejects invalid windows |
| Validation | Check that input has an allowed shape/value | A slot requires timezone-aware dates and valid duration |
| TypeScript | JavaScript with development-time types | PrivateCase interface in React |
| Component | A reusable interface unit | SignIn or SevaWorkerProfile |
| Hook | React state/lifecycle functionality | useState holds a form value; useEffect loads records |
| Context | Shared React values across components | AuthProvider and language provider |
| Routing | Select the code/view for a URL or intent | React Router pages; separate graph intent routing |
| State | Values describing current work | React state, graph state and persisted domain state have different lifetimes |
| Database | Organized persistent data | Mongo operational records |
| NoSQL | A broad category beyond relational-table-only models | Mongo BSON documents with nested arrays |
| Document | One structured Mongo record, or a file depending on context | assistance_cases record versus uploaded PDF bytes |
| Collection | A named group of Mongo records | seva_workers |
| Index | A lookup/uniqueness structure | Unique users.username and job due-time indexes |
| TTL | Time-to-live cleanup policy | Expired sessions are eventually removed, but access also checks expiry immediately |
| BSON | Mongo's typed binary document format | Stored native dates and nested case metadata |
| Authentication | Establish who is calling | Login creates an opaque session |
| Authorization | Decide what that actor can do | A citizen may read only their owned private case |
| Bearer token | A credential presented with a request | Authorization header, kept in tab memory |
| Opaque session | A token whose meaning is looked up server-side | Hashed token maps to Mongo session/user state |
| JWT | A signed structured token format | Not used for application sessions here |
| Scrypt | A password-hashing function with computational cost | Salted hash_password and constant-time verification |
| RBAC | Role-based access control | Admin can review verification; citizen cannot |
| Object-level access | Permission for this particular record | Worker assignment to a visit does not grant the entire linked case |
| Consent | Explicit permission for a defined action/use | Sharing necessary details with the assigned worker |
| Audit trail | Recorded actor/time/action history | Booking audit and case activity arrays |
| Idempotency | Repeating an intended action does not repeat its effect | Same creation key/payload returns existing owned case |
| Fingerprint | Stable representation identifying intended payload | Reused key with changed request data is rejected |
| Concurrency | Multiple operations happening at once | Two coordinators selecting overlapping slots |
| Compare-and-swap / CAS | Update only if the version still matches | A case save filters its previous revision |
| Atomic update | One indivisible database operation | Worker reservation overlap/capacity filter plus push |
| Transaction | A set of changes committed together | Do not claim universal multi-document transactions on this standalone Mongo design |
| Compensation | A corrective operation after a partial failure | Release a provisional calendar reservation when assignment cannot finish |
| Outbox | Durable pending work linked to a domain event | Reviewed visit completion syncs one case activity with a stable operation key |
| Scheduler / worker | Process that handles persisted due work | app.cases.worker polls reminders and visit automation |
| Retry | Attempt again after failure | Bounded provider retry or durable worker reconciliation |
| LLM | A model capable of generating/interpreting text | Optional Ollama or approved hosted adapter; no live inference claim |
| AI agent | A system performing a task through state/actions | Here, bounded graphs and deterministic assistance capabilities |
| Deterministic rule | A reproducible condition rather than generated judgment | Current verification must extend through the visit window |
| RAG | Retrieve evidence before grounded explanation | Reviewed government passages support the matcher |
| Fine-tuning | Changing a model's learned weights | Not performed by this project's source ingestion |
| Embedding | Numeric representation used to compare text | Local ONNX MiniLM query/chunk vectors |
| Vector | A sequence of numbers | Representation stored alongside a public chunk in Chroma |
| Vector database | Store/search numeric representations | Embedded Chroma PersistentClient |
| Semantic search | Search by meaning-like similarity | Insurance wording retrieves relevant reviewed passages |
| Cosine distance | A vector similarity measure | Chroma collection search, with distance threshold |
| Chunking | Split large text into retrievable passages | 1100-character chunks with 200-character overlap |
| Metadata | Information about information | Source URL, page, hash, dates and version |
| Provenance | Traceable origin/history of evidence | Reviewed official source identity and supporting quote |
| Citation | A reference to supporting evidence | Chunk/source ID, official URL, page and quotation |
| Hallucination | Unsupported generated content | Invented eligibility rules are rejected/withheld by evidence gates |
| Prompt injection | Untrusted text trying to redirect system behavior | A source passage cannot grant a model permission to assign a worker |
| LangGraph | A framework for stateful graph workflows | CaseOrchestrator StateGraph |
| Node | A processing function in a graph | load_context |
| Edge | A permitted transition between nodes | validate_result -> persist |
| Conditional edge | A branch selected from state | Supported case intent selects documents/followup/escalation/etc. |
| Handoff | Move work/context to a fixed collaborator | Authorized case delegates a scheme-match task |
| Checkpoint | Saved execution state for resumption | No LangGraph checkpointer is configured; domain records persist separately |
| Human-in-the-loop | People retain specified decisions | Coordinator confirmation and outcome review |
| OCR | Extract text from an image/scan | Optional Tesseract-dependent document path |
| Localization | Adapt interface language/formatting | hi/te dictionaries and India locale dates |
| Speech recognition / TTS | Convert speech to text / text to speech | Consented browser APIs with text fallback; physical behavior unverified |
| Mock | Controlled stand-in during a test | Fake provider transport avoids paid API calls |
| Unit test | Test a small behavior in isolation | Rule outcome or UI helper test |
| Integration test | Test connected implementation boundaries | Real Mongo ownership/concurrency checks |
| End-to-end test | Exercise a complete user flow | Chrome through React, FastAPI and synthetic records |
| Regression test | Keep a fixed defect from returning | Password whitespace or session-result leak checks |
| Git | Version-control system | Local commits preserve phase checkpoints |
| GitHub | Source/automation/publication platform | Confirmed main repository, Actions and static Pages |
| CI / CD | Continuous checks / delivery or deployment | Release checks versus separate Pages publication |
| Docker / container | Package/run an isolated application environment | Backend and Nginx images |
| Compose | Define multiple local services and volumes | Mongo/backend/worker/frontend rehearsal |
| Reverse proxy | Front server forwarding API requests | Nginx /api forwards to the backend service |
| DNS | Resolve a service/domain name to an address | Docker service-name refresh after backend replacement |
| Deployment / hosting | Publish software / provide its running environment | Static Pages is deployed; the full backend is not publicly hosted |
| Localhost | The machine making the request | A visitor's localhost is not the developer's API |
| Domain / subdomain | Address name / a name beneath another domain | dhroovs.github.io is the showcase host |
| Environment variable | Runtime/build configuration value | CHROMA_PATH or VITE_API_BASE_URL; VITE values are public browser configuration |
| HTTPS / TLS | Encrypted transport with certificate validation | Official-source downloads do not bypass TLS failures |
| CORS | Browser cross-origin access policy | Configured localhost frontend origins; not a substitute for authentication |
| Persistent volume | Storage that survives container replacement | Mongo/private files/Chroma directory in Compose |
| Cold start | Delay while an idle/stopped service starts | A free sleeping host may not process durable jobs continuously |
| Security advisory | Published dependency vulnerability information | Chroma findings intentionally fail the OSV gate |
| DPAPI | Windows-user data protection | Encrypted local synthetic demo credentials, never committed |

Practice a term by naming its authority boundary and one limitation. For example, an embedding helps retrieval but cannot authorize a private file; a graph coordinates work but cannot grant government approval.
