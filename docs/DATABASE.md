# Persistence, integrity and recovery

MongoDB holds users, hashed sessions, official catalogue/source metadata, minimal
conversation memory, cases, visits, worker calendars, organizations and admission
counters. Chroma holds only public reviewed text/vectors. Private documents are local
files referenced by random server-generated keys outside the frontend's public root.

Unique indexes protect user alias/ID, session hash, case/visit ID and owner creation
idempotency key, worker/organization IDs and source versions. TTL indexes clean expired
sessions, conversation memory and admission buckets. Runtime session expiry is checked
independently of delayed TTL cleanup. User role/activation is reloaded on each request;
`auth_version` invalidates old sessions after administrator changes.

Case and visit mutations use revision compare-and-swap plus receipts. One atomic
worker calendar update checks verification revision, expiry, capacity and overlap.
Audit notices and operation receipts are persisted with the winning case/visit CAS.
Completion outbox retries cannot duplicate case activity. Array/audit capacities and
query caps are bounded; larger production workloads require further scaling work.

Phase 5 changes are additive: new records get fields; old records use Pydantic defaults.
Existing missing user revisions are treated as zero on the first guarded update.
No destructive migration or real citizen data deletion was performed. Startup/readiness
initializes indexes; duplicate legacy data fails visibly rather than being silently removed.

## Backup and restore

Stop backend, scheduler and ingestion writers first. Keep MongoDB available for the
logical export. The operator CLI exports EJSON, indexes, private files and Chroma files
from a **quiesced** installation. It is not a concurrent distributed snapshot. Backups
contain sensitive hashes/documents: restrict access, encrypt offline storage, and do
not commit them. Sessions and transient admission records are excluded.

From backend, with a new backup directory:

```powershell
.\.venv\Scripts\python.exe -m scripts.backup backup ../backups/phase5-snapshot --confirm-quiesced
.\.venv\Scripts\python.exe -m scripts.backup restore ../backups/phase5-snapshot --target-database yojanasetu_restore_review --files-root ../backups/restored-files --confirm-quiesced
```

Restore refuses the original or a nonempty target database and an existing files root.
It checks collection hashes and counts, restores indexes and files, and never overwrites
the running database. A partial failure leaves the new target for investigation; use
a different new target after correcting the problem. Point an isolated backend to the
restored database/private/chroma paths, verify counts, ownership, file access and actual
vector retrieval, then authorize a cutover separately. Restored users must sign in again.

The automated drill verified synthetic Mongo records, unique indexes, session exclusion
and private/vector-directory fixture files. It did **not** certify a live multi-service
Chroma snapshot or production disaster recovery. Rehearse the full stopped-service
restore and source queries on the target platform before production.
