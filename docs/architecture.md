# Phase 1 architecture

Historical Phase 1 snapshot. Phase 2 integration and current boundaries are described
in [phase2.md](phase2.md); the Scheme Matcher is now implemented.

React Router pages call a JSON FastAPI API. Pydantic validates input; MongoRepository
uses PyMongo's AsyncMongoClient for persistent records. MongoDB is required; there
is no application fallback to in-memory storage. The test suite injects an isolated
test double. Health checks database reachability and returns 503 when unavailable.

Public scheme discovery uses literal substring search over up to 500 records.
This deliberately small catalogue needs indexed search and pagination before growth.
Development seeding is idempotent and only runs when APP_ENV=development and
ENABLE_DEMO_DATA=true. All three seed schemes are fictional, clearly labelled demos.
If MongoDB is unavailable at startup, start it and restart the API to seed data.

Cases and doorstep requests are blocked by default. Local demonstrations require
APP_ENV=development, ENABLE_DEV_CASE_ACCESS=true and a token of 32+ characters.
The browser sends an explicitly entered token in X-Dev-Token and retains it only
in component memory. It is never included in Vite environment configuration.
This shared development token provides no per-citizen ownership and must not be
used for public access. Bind both servers to loopback. Production disables these
endpoints regardless of the flag. No personal names, contact details, identity
numbers, attachments or home addresses are collected. Use fictional inputs only.

The agents package defines five Protocol contracts. None has an implementation.
LangGraph orchestration, model providers, ChromaDB retrieval, official document
ingestion and grounded eligibility matching belong to later approved work.
SchemeIngestionSource is the adapter boundary for verified data. Production
ingestion must validate source provenance, freshness, rights, schema and review
status; do not import demo records into a production database.

Before public use: add authentication, ownership checks and role authorization,
verified source ingestion, rate limiting, audit logging, retention controls,
backup/recovery, real translations and accessibility/user testing. No official
government application submission, approval, KYC, worker dispatch, reminders,
automated status transitions or notifications is implemented.

The coordinator page is a labelled placeholder. Dashboard links work but no
personal history exists. Doorstep records are stored without dispatch or a retrieval
endpoint. Language selection previews availability; Hindi/Telugu translation is
explicitly unavailable. Google Fonts is optional; system font fallbacks work offline.

The frontend locks patched router/build/test versions. A scoped minimatch override
in the lint tool dependency tree addresses an advisory; lint and build checks pass
with that override. Reassess the override on dependency updates.
