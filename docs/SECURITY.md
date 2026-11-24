# Security and privacy review

## Synthetic inspection isolation

Demo-only users reject password login and existing sessions outside development;
a real-Mongo regression verifies both paths and ordinary-account continuity.
Passwords are Windows-user DPAPI encrypted under ignored .tools/inspection-demo,
never committed/logged. Do not export the demo database into production. The app
binds to loopback; no public tunnel is started. See LOCAL_DEMO_ACCESS.md.

This is a local release candidate, not production security certification. The current
production gate is **blocked** by unresolved ChromaDB upstream advisories. See
[SECURITY_ADVISORIES.json](SECURITY_ADVISORIES.json), captured from OSV on 23 November
2026, and the upstream [Chroma security advisories](https://github.com/chroma-core/chroma/security/advisories).

orjson was upgraded to 3.11.6 and pytest to 9.2.0; their reported advisories cleared.
The re-scan checked 119 pinned packages and found only ChromaDB 1.5.9, also the latest
published PyPI version at the check. Four GHSA advisories (with PYSEC aliases) describe
high/critical HTTP-server authorization/code-injection paths. The app uses local
`PersistentClient`, fixed local embeddings and no exposed Chroma HTTP server or remote
model-repository configuration endpoint. These entry points are absent here, but the
package is not patched and this is not a global safety claim. Do not start/expose a
Chroma server. CI intentionally fails the Python advisory gate until resolved; there
is no silent ignore list. Public release needs an upstream fix or an independently
reviewed, explicitly approved risk decision. Nothing has been deployed.

## Controls verified locally

- Scrypt passwords with random salts and constant-time verification; opaque bearer
  sessions hashed in MongoDB, explicit expiry and logout revocation. Tokens stay in
  tab memory, not localStorage/cookies. Role/activation/version is checked per request.
- Citizen-only consented signup, bounded admission, no role parameter; staff elevation
  is admin-only, audited, revision-checked and revokes sessions. API cannot disable or
  demote existing administrators, preventing parallel last-admin removal. Operator
  governance is still necessary for administrator changes and recovery.
- Role and object ownership checks for cases, conversations, documents and visits.
  Unclaimed queues are minimized. Worker visibility is assigned/currently verified
  only, with address redaction and terminal access denial.
- Pydantic allowlists, bounded inputs, validated source URLs, private random file keys,
  PDF/image type/size/readability checks, executable-action rejection and image metadata
  stripping. Technical readability never establishes authenticity or KYC.
- Idempotency receipts, revision CAS, atomic calendar conflicts, durable deduplication,
  quiet hours, retention and a completion outbox. Disputed completion cannot be erased
  through an approval/cancellation/rescheduling shortcut.
- React text escaping, no untrusted HTML rendering, explicit CORS, no automatic bearer
  cookies (classic cookie CSRF is not the authentication model), private no-store
  responses and anti-framing/nosniff/referrer headers. Nginx adds CSP and request limits.
- Request logs contain method, route **template**, status, duration and generated request
  ID, never headers, queries, request bodies or private records. Prompt tracing is off.
- Models select validated evidence/fact IDs, never arbitrary tools or unsupported rules.
  Hosted calls require explicit approval. Speech has separate informed browser-processing
  consent; no audio is stored by the app. Native services may process speech externally.

## Remaining production work

Resolve dependency advisories, run container/Linux CI and deployment restore drills,
configure TLS, authenticated/encrypted MongoDB, private encrypted storage, encrypted
backups, managed secrets, monitoring and trusted proxy/rate policies. Add operational
account recovery, staff-verification governance, load/failure tests and professional
security/privacy review. The current directory/candidate caps target local use.

Never place secrets in `VITE_*`, Git, screenshots, logs or issue comments. `.env`,
data, downloads, models, backups and build artifacts are ignored. Account aliases
should not be personal names/contact data. Tests use synthetic records only. No Aadhaar
authentication, biometrics, covert tracking or official government submission exists.


## Beginner security model and role matrix

Authentication answers who is calling. Authorization answers what that caller may do to this object.
Opaque random bearer tokens are hashed in Mongo, checked for expiry and matched to a current active account.
There is no JWT parser here. Logout revokes the session; role changes increment auth_version. Public signup
creates only citizen accounts, with consent and alias restrictions. Scrypt hashes passwords with salts;
password whitespace is preserved rather than silently changed.

| Capability | Citizen | Worker | Coordinator | Administrator |
| --- | --- | --- | --- | --- |
| Read a private case | Own | Explicit case assignment | Responsible coordinator / permitted claim flow | Administrative access |
| Submit a private case | Own citizen identity | No | No | No citizen impersonation route |
| Review a checklist | No | No reviewer authority | Authorized responsible case | Authorized administrative case |
| Create a visit | Own with consent | No | No | No citizen impersonation route |
| Read a visit | Own | Current verified assignment; exact address gated by acceptance | Responsible coordinator / permitted claim | Administrative access |
| Accept/check in/submit outcome | No | Assigned accepted worker and valid stage/time | No worker impersonation | No worker impersonation |
| Assign/review visit outcome | No | No | Authorized confirmed review | Authorized confirmed review |
| Worker verification/user roles | No | Own profile/availability only | No admin verification authority | Guarded admin operations |
| Ingest official sources | No browser role | No browser role | No browser role | Operator CLI, not an admin-browser write endpoint |

Case worker assignment and visit worker assignment are different relations. Role alone does not confer
access to every private record. Hiding a button is only a UI convenience: an attacker can call HTTP directly,
so services recheck authority and exact object links. Graphs cannot bypass those same checks.

Source/model text is untrusted. Fixed intents, bounded calls, typed outputs, current evidence/hash checks
and quote validation reduce prompt-injection/unsupported-claim risk; they do not prove every possible
attack is solved. Rate limits, upload bounds, private storage, safe error/log projections, consent,
CAS/idempotency and audit support the overall design. This is not an independent penetration-test certificate.

Before public backend release, resolve the Chroma gate and review authenticated/encrypted Mongo, TLS,
secret management, upload scanning/retention, recovery/MFA, proxy admission policy, complete restore and
load/failure behavior. No government endorsement, Aadhaar KYC or automatic benefit determination is provided.
