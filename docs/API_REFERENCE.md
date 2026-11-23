# API reference - generated route inventory

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

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/admin/operations` | Operations |
| GET | `/api/admin/users` | Users |
| POST | `/api/admin/users/{user_id}` | Update |
| GET | `/api/ai/coverage` | Coverage |
| POST | `/api/ai/scheme-chat` | Chat |
| POST | `/api/ai/scheme-match` | Match |
| GET | `/api/ai/schemes/{scheme_id}/sources` | Sources |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Me |
| POST | `/api/auth/preferences` | Preferences |
| POST | `/api/auth/register` | Register |
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
| POST | `/api/doorstep-requests` | Doorstep |
| GET | `/api/health` | Health |
| GET | `/api/live` | Live |
| GET | `/api/ready` | Ready |
| GET | `/api/schemes` | Schemes |
| GET | `/api/schemes/{scheme_id}` | Scheme |
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
- Workers see only assigned cases/active visits with current verification; exact visit location is withheld before acceptance.
- Coordinators claim minimized queues, review documents/outcomes, schedule follow-ups, resolve referrals and confirm eligible assignments.
- Administrators manage user roles/activation, worker verification/expiry and organizations; operations returns sanitized configuration/status only.
- Public endpoints expose catalogue/source metadata and health, never private citizens, worker contacts or file paths.

Error responses: 401 session/credentials; 403 role; 404 unavailable or unowned object;
409 stale revision, conflicting reservation or invalid state; 415 file type; 422 validation;
429 admission limit; 503 database/provider configuration; 504 bounded workflow timeout.
Validation errors omit supplied values. Errors are not proof that an external provider delivered anything.
