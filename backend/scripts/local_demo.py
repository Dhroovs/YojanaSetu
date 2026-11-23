"""Windows-only isolated synthetic demo. Credentials are encrypted by Windows DPAPI."""

import argparse
import asyncio
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import pymupdf
from pymongo import AsyncMongoClient

from app.auth import hash_password
from app.cases.models import now_utc
from app.config import Settings

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / ".tools" / "inspection-demo"
MANIFEST = DIRECTORY / "manifest.json"
ACCESS = DIRECTORY / "access.dpapi"
API = "http://127.0.0.1:8000/api"
WEB = "http://localhost:5173"
ROLES = {
    "demo-citizen": "citizen",
    "demo-worker": "worker",
    "demo-volunteer": "worker",
    "demo-unverified": "worker",
    "demo-coordinator": "coordinator",
    "demo-admin": "admin",
}


def powershell(command, data=""):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        input=data,
        text=True,
        capture_output=True,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return result.stdout.strip()


def encrypt_access(accounts):
    encrypted = powershell(
        "$s=[Console]::In.ReadToEnd();"
        "ConvertFrom-SecureString (ConvertTo-SecureString $s -AsPlainText -Force)",
        json.dumps(accounts),
    )
    ACCESS.write_text(encrypted, encoding="utf-8")


def read_access():
    plain = powershell(
        "$s=ConvertTo-SecureString ([Console]::In.ReadToEnd().Trim());"
        "[System.Net.NetworkCredential]::new('', $s).Password",
        ACCESS.read_text(encoding="utf-8"),
    )
    return json.loads(plain)


def save(manifest):
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


async def prepare(settings, manifest, accounts):
    async with AsyncMongoClient(settings.mongodb_uri) as mongo:
        db = mongo[manifest["database"]]
        if await db.list_collection_names():
            raise RuntimeError("Refusing to overwrite a nonempty demo database")
        for name in ("schemes", "ai_sources"):
            query = {"is_demo": False} if name == "schemes" else {"verification_status": "verified"}
            rows = await mongo[settings.mongodb_database][name].find(query, {"_id": 0}).to_list(500)
            if not rows:
                raise RuntimeError("Reviewed official sources must already be ingested")
            await db[name].insert_many(rows)
        for alias, role in ROLES.items():
            await db.users.insert_one(
                {
                    "id": alias,
                    "username": alias,
                    "role": role,
                    "active": True,
                    "demo_only": True,
                    "language": "en",
                    "password_hash": hash_password(accounts[alias]),
                }
            )


def environment(settings, manifest):
    return dict(
        os.environ,
        APP_ENV="development",
        MONGODB_URI=settings.mongodb_uri,
        MONGODB_DATABASE=manifest["database"],
        CHROMA_PATH=str(DIRECTORY / "chroma"),
        DOCUMENT_STORAGE_PATH=str(DIRECTORY / "private-documents"),
        ENABLE_AI="true",
        ENABLE_DEMO_DATA="false",
        ENABLE_DEV_CASE_ACCESS="false",
        ENABLE_CITIZEN_REGISTRATION="true",
        ALLOW_HOSTED_LLM="false",
        LLM_PROVIDER="none",
        CORS_ORIGINS='["http://localhost:5173","http://127.0.0.1:5173"]',
        VITE_API_BASE_URL=API,
    )


def start(settings, manifest):
    # Never take over a port or terminate another process.
    for port in (8000, 5173):
        with socket.socket() as connection:
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(f"Port {port} is already occupied; no process was replaced")
    node = os.environ.get("NODE_BINARY", shutil.which("node"))
    if not node:
        raise RuntimeError("Set NODE_BINARY to the installed node.exe")
    env = environment(settings, manifest)
    commands = {
        "backend": (
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--no-access-log",
            ],
            ROOT / "backend",
        ),
        "frontend": (
            [
                node,
                "node_modules/vite/bin/vite.js",
                "--host",
                "127.0.0.1",
                "--port",
                "5173",
                "--strictPort",
            ],
            ROOT / "frontend",
        ),
    }
    manifest["processes"] = {}
    for name, (command, directory) in commands.items():
        with (DIRECTORY / (name + ".log")).open("ab") as output:
            process = subprocess.Popen(
                command,
                cwd=directory,
                env=env,
                stdout=output,
                stderr=output,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        manifest["processes"][name] = process.pid
        save(manifest)
    with httpx.Client(timeout=5, trust_env=False) as client:
        for url in (API + "/ready", WEB):
            for _ in range(60):
                try:
                    if client.get(url).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise RuntimeError("Startup failed; inspect local demo logs, no data removed")


def call(client, method, path, token=None, **kwargs):
    headers = {"Idempotency-Key": "demo-" + uuid4().hex}
    if token:
        headers["Authorization"] = "Bearer " + token
    headers.update(kwargs.pop("headers", {}))
    response = client.request(method, API + path, headers=headers, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Demo API {method} {path}: {response.status_code} {response.text[:300]}"
        )
    return response.json() if response.content else None


def start_scheduler(settings, manifest):
    with (DIRECTORY / "scheduler.log").open("ab") as output:
        process = subprocess.Popen(
            [sys.executable, "-m", "app.cases.worker", "--poll-seconds", "5"],
            cwd=ROOT / "backend",
            env=environment(settings, manifest),
            stdout=output,
            stderr=output,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    manifest["processes"]["scheduler"] = process.pid
    save(manifest)


def seed(settings, manifest, accounts):
    with httpx.Client(timeout=100, trust_env=False) as client:
        tokens = {
            alias: call(client, "POST", "/auth/login", json={"username": alias, "password": pwd})[
                "access_token"
            ]
            for alias, pwd in accounts.items()
        }
        citizen, coord, admin = (tokens["demo-" + r] for r in ("citizen", "coordinator", "admin"))
        slot = (now_utc() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
        window = {"start": slot.isoformat(), "end": (slot + timedelta(hours=1)).isoformat()}
        for alias in ("demo-worker", "demo-volunteer", "demo-unverified"):
            existing = client.get(
                API + f"/seva/workers/{alias}",
                headers={"Authorization": "Bearer " + tokens[alias]},
            )
            if existing.status_code == 200:
                continue
            if existing.status_code != 404:
                raise RuntimeError("Unable to inspect the synthetic worker profile")
            profile = call(
                client,
                "POST",
                f"/seva/workers/{alias}",
                tokens[alias],
                json={
                    "display_name": "Synthetic " + alias,
                    "kind": "ngo_volunteer" if alias == "demo-volunteer" else "field_worker",
                    "categories": ["document_assistance", "scheme_guidance"],
                    "languages": ["en", "hi", "te"],
                    "districts": ["Demo District"],
                },
            )
            if alias != "demo-unverified":
                profile = call(
                    client,
                    "POST",
                    f"/seva/workers/{alias}/verification",
                    admin,
                    json={
                        "revision": profile["revision"],
                        "status": "verified_internally",
                        "expires_at": (slot + timedelta(days=30)).isoformat(),
                        "confirmed": True,
                        "note": "Synthetic local demo review only; no government certification",
                    },
                )
            call(
                client,
                "POST",
                f"/seva/workers/{alias}/availability",
                tokens[alias],
                json={
                    "revision": profile["revision"],
                    "slots": [window],
                    "note": "Synthetic availability",
                },
            )
        case = call(
            client,
            "POST",
            "/cases",
            citizen,
            json={
                "scheme_id": "pmsby",
                "assistance_type": "Synthetic document assistance demo",
            },
        )
        path = "/cases/" + case["id"]
        case = call(
            client,
            "POST",
            path + "/assignment",
            coord,
            json={
                "revision": case["revision"],
                "coordinator_id": "demo-coordinator",
                "confirmed": True,
                "note": "Synthetic demo coordinator claim",
            },
        )
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((60, 60), "SYNTHETIC DEMO FILE - NO PERSONAL INFORMATION")
            content = pdf.tobytes()
        (DIRECTORY / "synthetic-sample.pdf").write_bytes(content)
        assert case["checklist"], "Official PDF checklist missing"
        case = call(
            client,
            "POST",
            path + "/documents",
            citizen,
            params={"revision": case["revision"], "item_id": case["checklist"][0]["id"]},
            content=content,
            headers={"Content-Type": "application/pdf"},
        )
        case = call(
            client,
            "POST",
            path + "/followups",
            coord,
            json={
                "revision": case["revision"],
                "reason": "manual",
                "due_at": (now_utc() + timedelta(seconds=15)).isoformat(),
                "note": "Synthetic scheduled demo follow-up",
            },
        )
        case = call(
            client,
            "POST",
            path + "/assist",
            citizen,
            json={
                "revision": case["revision"],
                "intent": "escalation",
                "question": "Please request human assistance for this synthetic case",
                "apply_changes": True,
            },
        )

        # Preferences affect this synthetic record only. The actual scheduler delivers it.
        async def no_quiet_hours():
            async with AsyncMongoClient(settings.mongodb_uri) as mongo:
                await mongo[manifest["database"]].assistance_cases.update_one(
                    {"id": path.rsplit("/", 1)[1]},
                    {"$set": {"preferences.quiet_start": 0, "preferences.quiet_end": 0}},
                )

        asyncio.run(no_quiet_hours())
        booking = call(
            client,
            "POST",
            "/seva/requests",
            citizen,
            json={
                "category": "document_assistance",
                "case_id": path.rsplit("/", 1)[1],
                "scheme_id": "pmsby",
                "description": "Synthetic doorstep checklist guidance",
                "preferred_window": window,
                "location": {
                    "district": "Demo District",
                    "mandal": "Demo Mandal",
                    "village": "Demo Village",
                    "address": "Synthetic demonstration location",
                },
                "share_with_assigned_worker": True,
                "preferences": {"in_app": True, "quiet_start": 0, "quiet_end": 0, "language": "en"},
            },
        )
        visit = "/seva/requests/" + booking["id"]
        for action in ("claim", "approve"):
            booking = call(
                client,
                "POST",
                visit + "/actions",
                coord,
                json={
                    "revision": booking["revision"],
                    "action": action,
                    "confirmed": True,
                    "note": "Synthetic demo review",
                },
            )
        booking = call(
            client,
            "POST",
            visit + "/assignment",
            coord,
            json={
                "revision": booking["revision"],
                "worker_id": "demo-worker",
                "override_reason": "Synthetic demo selects the field-worker role for inspection",
                "window": window,
                "confirmed": True,
                "note": "Synthetic demo assignment",
            },
        )
        booking = call(
            client,
            "POST",
            visit + "/actions",
            tokens["demo-worker"],
            json={
                "revision": booking["revision"],
                "action": "accept",
                "confirmed": True,
                "note": "Synthetic demo acceptance",
            },
        )
        manifest["case_id"] = path.rsplit("/", 1)[1]
        manifest["visit_id"] = booking["id"]
        manifest["seeded"] = True
        save(manifest)
        for token in tokens.values():
            call(client, "POST", "/auth/logout", token)


def complete_visit(manifest, accounts):
    """Create a second visit with an explicitly simulated, human-reviewed outcome."""
    if manifest.get("completed_visit_id"):
        return
    with httpx.Client(timeout=60, trust_env=False) as client:
        tokens = {}
        for alias in ("demo-citizen", "demo-worker", "demo-coordinator"):
            tokens[alias] = call(
                client,
                "POST",
                "/auth/login",
                json={
                    "username": alias,
                    "password": accounts[alias],
                },
            )["access_token"]
        citizen, worker, coord = (tokens["demo-" + r] for r in ("citizen", "worker", "coordinator"))
        slot = now_utc().replace(microsecond=0) + timedelta(minutes=10)
        window = {"start": slot.isoformat(), "end": (slot + timedelta(hours=1)).isoformat()}
        profile = call(client, "GET", "/seva/workers/demo-worker", worker)
        call(
            client,
            "POST",
            "/seva/workers/demo-worker/availability",
            worker,
            json={
                "revision": profile["revision"],
                "slots": profile["availability"] + [window],
                "note": "Synthetic demonstration window; no physical visit",
            },
        )
        b = call(
            client,
            "POST",
            "/seva/requests",
            citizen,
            json={
                "category": "document_assistance",
                "case_id": manifest["case_id"],
                "scheme_id": "pmsby",
                "description": "Simulated demo visit, no physical service",
                "preferred_window": window,
                "location": {
                    "district": "Demo District",
                    "mandal": "Demo Mandal",
                    "village": "Demo Village",
                    "address": "Synthetic demonstration location",
                },
                "share_with_assigned_worker": True,
                "preferences": {"in_app": True, "quiet_start": 0, "quiet_end": 0, "language": "en"},
            },
        )
        path = "/seva/requests/" + b["id"]
        for action, token in (("claim", coord), ("approve", coord)):
            b = call(
                client,
                "POST",
                path + "/actions",
                token,
                json={
                    "revision": b["revision"],
                    "action": action,
                    "confirmed": True,
                    "note": "Synthetic simulation review",
                },
            )
        b = call(
            client,
            "POST",
            path + "/assignment",
            coord,
            json={
                "revision": b["revision"],
                "worker_id": "demo-worker",
                "window": window,
                "confirmed": True,
                "note": "Synthetic simulated service assignment",
                "override_reason": "Synthetic demo field-worker selection",
            },
        )
        for action in ("accept", "en_route", "check_in", "submit_outcome"):
            body = {
                "revision": b["revision"],
                "action": action,
                "confirmed": True,
                "note": "SIMULATED demonstration only; no real visit or official submission",
            }
            if action == "submit_outcome":
                body.update(
                    services_performed=["document_assistance"],
                    task_checklist=["Explained synthetic checklist in demonstration"],
                )
            b = call(client, "POST", path + "/actions", worker, json=body)
        b = call(
            client,
            "POST",
            path + "/actions",
            coord,
            json={
                "revision": b["revision"],
                "action": "confirm_completion",
                "confirmed": True,
                "note": "Reviewed synthetic simulation only; no official approval",
            },
        )
        b = call(
            client,
            "POST",
            path + "/actions",
            citizen,
            json={
                "revision": b["revision"],
                "action": "feedback",
                "rating": 5,
                "note": "Synthetic demonstration feedback; no real citizen",
            },
        )
        assert b["stage"] == "visit_completed" and b["outcome"]["reviewed_by"]
        manifest["completed_visit_id"] = b["id"]
        save(manifest)
        for token in tokens.values():
            call(client, "POST", "/auth/logout", token)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "access", "status"])
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("This local demo helper uses Windows DPAPI; do not deploy it")
    if args.action == "access":
        # Only an explicit operator command displays passwords. Never invoke in CI/log capture.
        for alias, password in read_access().items():
            print(f"{alias} ({ROLES[alias]}): {password}")
        return
    if args.action == "status":
        print(MANIFEST.read_text(encoding="utf-8"))
        return
    settings = Settings()
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        manifest, accounts = json.loads(MANIFEST.read_text()), read_access()
    else:
        manifest = {
            "database": "yojanasetu_inspection_demo_" + uuid4().hex,
            "synthetic_only": True,
            "frontend": WEB,
            "api_docs": API[:-4] + "/docs",
        }
        accounts = {alias: secrets.token_urlsafe(24) for alias in ROLES}
        encrypt_access(accounts)
        save(manifest)
        # Copy only the public vector catalogue, never citizens/documents/sessions.
        shutil.copytree(Path(settings.chroma_path).resolve(), DIRECTORY / "chroma")
        asyncio.run(prepare(settings, manifest, accounts))
    start(settings, manifest)
    if not manifest.get("seeded"):
        seed(settings, manifest, accounts)
    complete_visit(manifest, accounts)
    start_scheduler(settings, manifest)
    print(f"Demo running: {WEB}; API docs: {manifest['api_docs']}")
    print("Synthetic database only. To inspect temporary credentials locally:")
    print("  .\\.venv\\Scripts\\python.exe -m scripts.local_demo access")
    print("Do not copy the encrypted access file or demo database into production.")


if __name__ == "__main__":
    main()
