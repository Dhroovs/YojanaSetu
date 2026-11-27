# Inspect the running synthetic platform

Frontend: **http://localhost:5173/**. API documentation: **http://127.0.0.1:8000/docs**.
These addresses work on the development PC, not on a remote interviewer's computer.
Health/readiness and the frontend returned HTTP 200 during final verification.

## Active WSL demo (27 November 2026)

The current running demo uses Ubuntu 24.04 under WSL2 because Windows Smart App
Control blocked unsigned native Python/Git libraries. Windows protection remains
enabled. The original Windows database, documents and encrypted credentials are
preserved; the Linux demo has a separate synthetic database and separate passwords.

From your own PowerShell terminal, display the Linux demo passwords locally:

```powershell
wsl -d Ubuntu-24.04 -u yojana -- bash /mnt/e/YojanaSetu/YojanaSetu/backend/scripts/wsl_demo.sh access
```

Do not paste that output into chat or screenshots. Choose `demo-citizen` first;
the remaining aliases and roles are listed below. Linux credentials use owner-only
filesystem permissions (0600 file, 0700 directory), not Windows DPAPI encryption.

After a later PC restart, start the already configured runtime with:

```powershell
wsl -d Ubuntu-24.04 -u yojana -- bash /mnt/e/YojanaSetu/YojanaSetu/backend/scripts/wsl_demo.sh start
```

Use `status` instead of `start` to inspect the non-secret process manifest. The
launcher starts isolated MongoDB on loopback port 27018, verifies its database
directory, copies current frontend source into the Linux runtime and starts the
backend, frontend and worker. It requires the installed local Node 24, Python venv
and reviewed source catalogue; it is not a fresh-machine installer. It refuses
occupied application ports. Files live under the Linux user's
`~/.local/share/yojanasetu-runtime` and `~/.local/share/yojanasetu-inspection-demo`.

Verification on 27 November: backend 108/108 tests passed in 46.08 seconds; frontend
25/25 tests, lint and build passed; 16 Chrome screenshots and real role/RAG/reminder/
private-case assertions passed with zero JavaScript errors. Pytest emitted one
cache-permission warning for the Windows checkout; future runs can use
`-o cache_dir=/home/yojana/.cache/yojanasetu-pytest`.
Four reviewed source snapshots produced 28 real ONNX-backed chunks. A live
government-source download failed certificate validation; TLS validation remains
enabled, and the restored catalogue uses the preserved 23 November snapshots.
This does not resolve the existing upstream Chroma security advisories or deploy
a public backend. No paid services or hosted model calls were used.

## Original Windows demo

The inspection environment uses a dedicated random `yojanasetu_inspection_demo_*`
database and a copied public vector index in `.tools/inspection-demo`. Existing citizen
records, sessions and private documents were not copied, overwritten or deleted.
All seeded cases, addresses, files and visits are synthetic. A completed visit is
explicitly marked as a simulation, not real field service or government submission.
The development app has no shared-token anonymous case access and no hosted model.

In a normal Windows PowerShell terminal, reveal the temporary role passwords locally:

```powershell
Set-Location E:\YojanaSetu\YojanaSetu\backend
.\.venv\Scripts\python.exe -m scripts.local_demo access
```

Run this only in your own terminal; do not paste its output into chat, screenshots,
CI or permanent logs. Each password is randomly generated and stored only in a
Windows-user DPAPI-encrypted local file; it is not in Git. This sandbox cannot always
access your Windows profile; use the ordinary signed-in Windows terminal for access.
Do not copy `.tools/inspection-demo` or its encrypted access file to another machine.

| Alias | Role / inspection |
| --- | --- |
| `demo-citizen` | `/dashboard`: cases, PDF checklist, real RAG via Scheme assistant, reminders/escalations. SevaSetu: future assigned visit and reviewed simulated completion/feedback. |
| `demo-worker` | `/seva`: future assigned appointment; `/seva/profile`: internally reviewed field-worker profile/calendar. A visit assignment does not grant private-case access. |
| `demo-volunteer` | Worker role with `ngo_volunteer` profile kind, declared availability and internal verification. This is not a separate privileged auth role. |
| `demo-unverified` | Pending-verification worker profile; ineligible for assignment. |
| `demo-coordinator` | `/coordinator` for owned review/referral queues; `/seva` for assigned requests, ranking, human approval and visit outcome review. |
| `demo-admin` | `/admin` safe user/operations screens; `/seva/workers` internal verification/service areas; `/sources` provenance. |

Accounts marked `demo_only` cannot log in or use existing sessions outside
`APP_ENV=development`; the new real-Mongo regression test covers both paths.
Never promote these accounts, files or database into a production dataset.

Use Sign out on My account before switching roles. A hard refresh clears memory-only
bearer sessions and requires another login. The existing sign-in limit is 10 attempts
per minute per process/IP, so rapid repeated role switches may need a one-minute wait.

## Restart after a machine/service stop

Start the existing portable Mongo with the commands in LOCAL_SETUP_WINDOWS.md first.
Only if ports 8000/5173 are free and the old demo scheduler is stopped:

```powershell
Set-Location E:\YojanaSetu\YojanaSetu\backend
$env:NODE_BINARY='C:\Users\dhroo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
.\.venv\Scripts\python.exe -m scripts.local_demo start
.\.venv\Scripts\python.exe -m scripts.local_demo status
```

The helper preserves its existing random database/access data and refuses occupied
ports. It starts loopback backend/frontend, then the worker after fixture provisioning,
so worker revisions cannot race fixture setup. It does not stop unrelated processes.
Logs and a non-secret PID/database manifest stay under `.tools/inspection-demo`.
On a partial first-time setup failure, preserve that directory/database and inspect
the last error; do not automatically delete or overwrite it. A safe resumable fixture
repair may be required. Temporary initial setup errors were repaired in this run.

Verify the running demo and regenerate password-free synthetic screenshots:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_inspection_demo
```

This verifier performs a synthetic admin review-note update, login/logout, database
checks and local matching. It does not send messages or call a paid model. Its report
is `artifacts/inspection-demo-report.json`; screenshots are in `docs/demo-evidence`.
The background worker keeps running while you inspect the app; it ends if this PC
shuts down or the execution host terminates its processes.
