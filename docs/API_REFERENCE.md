# API reference - generated route inventory

## Demo account guard

Both /api/auth/login and existing bearer-session checks reject accounts marked
demo_only outside APP_ENV=development. No public endpoint provisions staff/demo roles.
The local helper is operator-only and is not an HTTP API.

This table is generated from the implemented FastAPI OpenAPI schema. It does not
claim every optional/external operation has been runtime-tested. See TESTING.md and
FINAL_HANDOFF.md for executed scope. Interactive local schemas are at `/docs`.

Private operations require `Authorization: Bearer ...`. Matching also sends an
independent `X-Session-Key`; authenticated matching works without a development
secret. Anonymous legacy demos require explicitly enabled development mode/token.

Case/visit actions use `Idempotency-Key` and current revision; profile/admin updates
use revision CAS. A changed payload/revision replay is rejected. Public registration
accepts aliases/password/consent/language only and never a role. All admin endpoints
require an active admin. Account-role changes revoke sessions and cannot remove an
existing administrator. Source ingestion/configuration secrets remain operator-only.

## Administrator operations

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/admin/operations` | Operations |
| GET | `/api/admin/users` | Users |
| POST | `/api/admin/users/{user_id}` | Update |

## Sources and Scheme Matcher

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/ai/coverage` | Coverage |
| POST | `/api/ai/scheme-chat` | Chat |
| POST | `/api/ai/scheme-match` | Match |
| GET | `/api/ai/schemes/{scheme_id}/sources` | Sources |

## Authentication and account preferences

| Method | Path | Summary |
| --- | --- | --- |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Me |
| POST | `/api/auth/preferences` | Preferences |
| POST | `/api/auth/register` | Register |

## Private cases and coordinator queues

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/cases` | Cases |
| POST | `/api/cases` | Create Case |
| GET | `/api/cases/{case_id}` | Get Case |
| GET | `/api/cases/{case_id}/activity` | Activity |
| POST | `/api/cases/{case_id}/assignment` | Assignment |
| POST | `/api/cases/{case_id}/assist` | Assist |
| GET | `/api/cases/{case_id}/checklist` | Checklist |
| POST | `/api/cases/{case_id}/checklist/refresh` | Refresh |
| POST | `/api/cases/{case_id}/documents` | Upload |
| GET | `/api/cases/{case_id}/documents/{document_id}/content` | Content |
| POST | `/api/cases/{case_id}/documents/{document_id}/delete` | Delete Document |
| POST | `/api/cases/{case_id}/documents/{document_id}/review` | Review |
| POST | `/api/cases/{case_id}/escalations/{escalation_id}` | Escalation |
| POST | `/api/cases/{case_id}/flags` | Flag |
| POST | `/api/cases/{case_id}/followups` | Followup |
| POST | `/api/cases/{case_id}/notices/{notice_id}/acknowledge` | Acknowledge Notice |
| POST | `/api/cases/{case_id}/preferences` | Preferences |
| POST | `/api/cases/{case_id}/reminders/{reminder_id}/acknowledge` | Acknowledge |
| POST | `/api/cases/{case_id}/stage` | Stage |
| GET | `/api/coordinator/queue` | Queue |
| GET | `/api/coordinator/staff` | Staff |

## Legacy development intake

| Method | Path | Summary |
| --- | --- | --- |
| POST | `/api/doorstep-requests` | Doorstep |

## Health and public catalogue

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/health` | Health |
| GET | `/api/live` | Live |
| GET | `/api/ready` | Ready |
| GET | `/api/schemes` | Schemes |
| GET | `/api/schemes/{scheme_id}` | Scheme |

## SevaSetu visits, workers and organizations

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/seva/organizations` | Organizations |
| POST | `/api/seva/organizations` | Organization |
| POST | `/api/seva/organizations/{organization_id}` | Edit Organization |
| GET | `/api/seva/requests` | Requests |
| POST | `/api/seva/requests` | Create |
| GET | `/api/seva/requests/{booking_id}` | Detail |
| POST | `/api/seva/requests/{booking_id}/actions` | Action |
| POST | `/api/seva/requests/{booking_id}/agent` | Agent |
| POST | `/api/seva/requests/{booking_id}/assignment` | Assign |
| POST | `/api/seva/requests/{booking_id}/notifications/{notification_id}/acknowledge` | Acknowledge |
| POST | `/api/seva/requests/{booking_id}/preferences` | Preferences |
| GET | `/api/seva/workers` | Workers |
| GET | `/api/seva/workers/{worker_id}` | Worker |
| POST | `/api/seva/workers/{worker_id}` | Profile |
| POST | `/api/seva/workers/{worker_id}/availability` | Available |
| POST | `/api/seva/workers/{worker_id}/profile` | Edit Worker |
| POST | `/api/seva/workers/{worker_id}/verification` | Verify |

## Selected permission boundaries

- Citizens create/read owned cases and visits, upload private documents, change their own preferences, acknowledge notices and give feedback.
- Workers see only explicitly assigned cases; active visit access additionally requires current verification and assignment. Exact visit location is withheld before acceptance.
- Coordinators claim minimized queues, review documents/outcomes, schedule follow-ups, resolve referrals and confirm eligible assignments.
- Administrators manage user roles/activation, worker verification/expiry and organizations; operations returns sanitized configuration/status only.
- Public endpoints expose catalogue/source metadata and health, never private citizens, worker contacts or file paths.

Error responses: 401 session/credentials; 403 role; 404 unavailable or unowned object;
409 stale revision, conflicting reservation or invalid state; 415 file type; 422 validation;
429 admission limit; 503 database/provider configuration; 504 bounded workflow timeout.
Validation errors omit supplied values. Errors are not proof that an external provider delivered anything.


## HTTP tutorial and important contracts

GET reads a representation; POST creates a resource or submits one of the explicit guarded actions.
PUT commonly replaces a resource and PATCH commonly partially updates one, but neither is implemented here.
DELETE is also not exposed in the current route inventory. Private document deletion is POST to its /delete
action with confirmation; listing DELETE in CORS allowed methods does not create a DELETE endpoint.

The examples below are sanitized, abridged teaching shapes, not captured personal records or complete schemas.

| Method and actual route | Purpose and required authority | Implementation |
| --- | --- | --- |
| GET /api/schemes?q=PMSBY | Public catalogue search | main.py / repositories.py |
| POST /api/auth/register | Public citizen-only registration, consent; no role input | auth.py |
| POST /api/auth/login | Alias/password -> expiring opaque bearer, never JWT | auth.py |
| POST /api/ai/scheme-match | Individual session plus X-Session-Key, or explicitly permitted dev access | ai/api.py / ai/service.py |
| POST /api/cases | Authenticated citizen creates own private case | main.py / cases/service.py |
| POST /api/cases/{case_id}/assist | Authorized case actor; supported intent/apply_changes rules | cases/api.py / agents/case_orchestrator.py |
| POST /api/cases/{case_id}/documents | Authorized upload, revision/item query and raw supported bytes | cases/api.py / cases/storage.py |
| GET /api/coordinator/queue | Staff queue; unassigned/minimal queue has stricter reviewer rules | cases/api.py |
| POST /api/seva/requests | Citizen owner with future window and consent | seva/api.py / seva/service.py |
| POST /api/seva/requests/{booking_id}/assignment | Authorized coordinator/admin, confirmed current eligible reservation | seva/service.py / seva/store.py |
| POST /api/seva/requests/{booking_id}/actions | Action-specific owner/worker/reviewer and stage checks, not any logged-in role | seva/service.py |
| POST /api/seva/workers/{worker_id}/verification | Admin review, revision, note, confirmation and expiry/evidence rules | seva/service.py |
| GET /api/admin/operations | Admin-only safe health/configuration view | admin.py |

### Registration and login

```json
{"username":"synthetic-citizen","password":"<choose-a-private-12-plus-character-password>","consent":true,"language":"en"}
```

Registration responds with an actor shape, not a token or password. Login accepts username/password only
and returns access_token, token_type, expires_at, user and language. Never log or publish a real token.

### Source-grounded question

```http
POST /api/ai/scheme-match
Authorization: Bearer <session-token>
X-Session-Key: <independent-32-plus-character-session-key>
Content-Type: application/json
```

```json
{"question":"PMSBY accident insurance enrolment assistance","profile":{"age":30,"state":"Telangana"}}
```

The structured response has conversation_id, profile, message, recommendations, follow_up_questions,
warnings, mode, trace and model_usage. A recommendation has scheme identity, eligibility status,
condition results and evidence. Do not hard-code an eligible outcome for partial source coverage.

### Create and mutate a private case

```json
{"scheme_id":"pmsby","assistance_type":"Document checklist help"}
```

POST /api/cases also needs a bearer and Idempotency-Key. A representative response subset is:

```json
{"id":"synthetic-case-reference","owner_id":"current-actor-id","scheme_id":"pmsby","revision":0,"checklist":[]}
```

The empty checklist is only a shape illustration, not a claim about the actual PMSBY source checklist.
Subsequent actions use the latest returned revision and a new key for a new intended action. Replaying an
unchanged intended action reuses its key; reusing a key with changed payload fails. Uploads send raw bytes,
not a JSON file path, to /documents?item_id=...&revision=... with the real supported Content-Type.

### Visit assignment

```json
{"revision":2,"worker_id":"synthetic-worker-id","window":{"start":"2099-01-01T06:30:00Z","end":"2099-01-01T07:30:00Z"},"confirmed":true,"note":"Reviewed synthetic request","override_reason":""}
```

The example's date/ID/revision are illustrative and must be replaced with actual current authorized state.
A non-top-ranked selection needs an explanatory override, but no override can bypass eligibility/conflicts.
Responses expose a role-filtered booking view, never a guarantee of government certification.

## Complete request-response path

React privateApi serializes JSON -> FastAPI route validates -> current_actor resolves current account ->
service checks role/object/stage -> store performs query/CAS/reservation -> response model/view limits fields ->
React renders success or a safe error. Check [architecture](ARCHITECTURE.md) and the current /docs schema
rather than guessing fields from an old UI screenshot.
