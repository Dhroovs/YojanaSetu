# Deployment preparation - no deployment performed

Dockerfiles, `compose.yaml`, Nginx same-origin proxy, health dependency ordering,
named persistence volumes, non-root application users, a separate scheduler and
GitHub Actions gates are authored. Compose and workflow YAML parsed successfully.
**Docker is not installed in this environment:** no image build, Compose startup or
Linux container workflow was executed here. Remote GitHub Actions was not run or pushed.
Do not represent these configurations as runtime-verified.

Public release is additionally blocked by unpatched ChromaDB advisories; see SECURITY.md.
The following is a local deployment rehearsal after installing Docker, not authorization
to publish, create cloud resources or incur charges:

```powershell
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://localhost:8080/api/ready
docker compose exec backend python -m app.cases.cli --username local-admin --role admin
```

Only frontend port 8080 is published, bound to loopback. MongoDB/backend have no host
ports. Local Compose Mongo has no authentication and must not be repurposed unchanged
for production. Application data includes private files and local Chroma; model cache
has a separate volume. The worker shares durable Mongo/private storage. Source ingestion
is operator-only and should run with serving/vector writers stopped. Fresh containers
need reviewed source ingestion and an embedding cache before useful RAG results.

For production, pin image digests after validation, configure managed secrets rather
than committing `.env`, use authenticated/encrypted MongoDB, TLS at a maintained reverse
proxy, reviewed CORS, private encrypted object storage and encrypted backups. Do not
assume free hosting supports persistent vectors/files, background jobs or local models.
Profile CPU/RAM/disk and concurrency on the target infrastructure before sizing it.

Uvicorn lifespan closes Mongo; the worker waits for an in-flight sweep then handles
termination using a stop event. Docker init/grace periods are configured. JSON request
logs expose generated IDs, route templates/status/latency only. Monitor `/api/live`,
`/api/ready`, worker exit/retry logs, due-job counts in admin operations, disk capacity,
backup age, source freshness and provider failure rates. Do not log citizen payloads.

## Backup, rollout and rollback

Use the quiesced backup/new-target restore process in DATABASE.md and rehearse actual
Mongo/private-file/Chroma retrieval on the target. Record the current Git revision,
image digest, dependency lock and configuration version before rollout. Use an isolated
staging database and volumes; run the acceptance tests and manual demo there.

If a release fails, stop application writers, retain the failed environment for diagnosis,
and run the previous reviewed image/configuration against its compatible snapshot or
a newly restored target. Do not force a database downgrade, overwrite live volumes,
run `docker compose down -v`, or restore onto existing data. Cutover/rollback and any
external infrastructure change require the owner's explicit approval. Keep sessions
revoked after restore. No destructive migration was added in Phase 5.

CI on push/PR runs backend/Mongo tests, frontend checks/build/audit and container builds.
The Python advisory check is intentionally a failing gate while Chroma advisories remain.
CI success has not been observed remotely. Before release, resolve or obtain independently
reviewed approval for that risk and verify container builds, health, persistence, restore,
browser workflows and shutdown on the actual target.
