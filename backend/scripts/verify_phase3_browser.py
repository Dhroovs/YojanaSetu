"""Isolated synthetic Chrome workflow. Never provisions test users in the live database."""

import asyncio
import os
import secrets
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pymupdf
from playwright.sync_api import expect, sync_playwright
from pymongo import AsyncMongoClient

from app.auth import hash_password
from app.cases.automation import process_due
from app.cases.models import now_utc
from app.cases.runtime import PrivateRuntime
from app.config import Settings
from scripts.verify_browser import wait_for

ROOT = Path(__file__).resolve().parents[2]


def main():
    settings = Settings()
    name = "yojanasetu_phase3_browser_" + uuid4().hex
    password = secrets.token_urlsafe(24)
    storage = ROOT / ".tools" / ("phase3-files-" + uuid4().hex)
    fixture_settings = Settings(
        _env_file=None,
        mongodb_uri=settings.mongodb_uri,
        mongodb_database=name,
        document_storage_path=str(storage),
    )
    case_id = None

    async def setup():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            db = mongo[name]
            for alias, role in [("test-citizen", "citizen"), ("test-coordinator", "coordinator")]:
                await db.users.insert_one(
                    {
                        "id": alias,
                        "username": alias,
                        "role": role,
                        "password_hash": hash_password(password),
                        "active": True,
                    }
                )
            await db.schemes.insert_one(
                {
                    "id": "synthetic-checklist",
                    "title": "Synthetic test-only checklist",
                    "category": "TEST ONLY",
                    "summary": "Synthetic isolated browser fixture",
                    "is_demo": False,
                    "eligibility": [],
                    "documents": ["Synthetic household record"],
                    "guidance": [],
                    "source_references": ["synthetic-source"],
                }
            )
            await db.ai_sources.insert_one(
                {
                    "source_id": "synthetic-source",
                    "verification_status": "verified",
                    "index_version": "test-version",
                    "required_documents": ["Synthetic household record"],
                    "field_evidence": {
                        "required_documents": "Synthetic isolated fixture, not government data."
                    },
                }
            )

    async def deliver():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            db = mongo[name]
            now = now_utc()
            await db.assistance_cases.update_one(
                {"id": case_id},
                {
                    "$set": {
                        "preferences.quiet_start": 0,
                        "preferences.quiet_end": 0,
                        "followups.$[job].due_at": now,
                        "next_automation_at": now,
                    }
                },
                array_filters=[{"job.status": "scheduled", "job.reason": "manual"}],
            )
            runtime = PrivateRuntime(db, fixture_settings)
            await runtime.initialize()
            await process_due(runtime.cases, now)

    async def cleanup():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            runtime = PrivateRuntime(mongo[name], fixture_settings)
            rows = await mongo[name].assistance_cases.find({}).to_list(10)
            for row in rows:
                for doc in row.get("documents", []):
                    runtime.storage.delete(doc["storage_key"])
            await mongo.drop_database(name)
        if storage.exists():
            storage.rmdir()

    asyncio.run(setup())
    env = dict(
        os.environ,
        APP_ENV="development",
        MONGODB_DATABASE=name,
        MONGODB_URI=settings.mongodb_uri,
        DOCUMENT_STORAGE_PATH=str(storage),
        ENABLE_DEMO_DATA="false",
        VITE_API_BASE_URL="http://127.0.0.1:8003/api",
        CORS_ORIGINS='["http://localhost:5176"]',
    )
    processes, errors = [], []
    try:
        for command, cwd in [
            (
                [
                    str(ROOT / "backend/.venv/Scripts/python.exe"),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8003",
                ],
                ROOT / "backend",
            ),
            (
                [
                    os.environ.get("NODE_BINARY", "node"),
                    "node_modules/vite/bin/vite.js",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "5176",
                    "--strictPort",
                ],
                ROOT / "frontend",
            ),
        ]:
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            )
        wait_for("http://127.0.0.1:8003/api/health")
        wait_for("http://localhost:5176")
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((60, 60), "SYNTHETIC TEST DOCUMENT - no identity numbers")
            data = pdf.tobytes()
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get(
                    "CHROME_BINARY", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                ),
                headless=True,
            )
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("dialog", lambda d: d.accept())

            def login(alias):
                page.goto("http://localhost:5176/login")
                page.get_by_label("Account alias").fill(alias)
                page.get_by_label("Password", exact=True).fill(password)
                page.get_by_role("button", name="Sign in securely").click()
                expect(
                    page.get_by_role("heading", name="My private assistance cases")
                ).to_be_visible()

            def logout():
                page.get_by_role("link", name="My account", exact=True).click()
                page.get_by_role("button", name="Sign out", exact=True).click()
                expect(page.get_by_role("button", name="Sign in securely")).to_be_visible()

            login("test-citizen")
            page.get_by_label("Scheme").select_option("synthetic-checklist")
            page.get_by_role("button", name="Create my case").click()
            expect(
                page.get_by_role("heading", name="synthetic-checklist", exact=True)
            ).to_be_visible()
            case_id = page.url.rsplit("/", 1)[-1]
            page.get_by_label("Checklist item").select_option(index=1)
            page.get_by_label("Synthetic or redacted file").set_input_files(
                {"name": "synthetic.pdf", "mimeType": "application/pdf", "buffer": data}
            )
            page.get_by_role("button", name="Upload securely / retry").click()
            expect(
                page.get_by_text("needs human review · technically readable", exact=True)
            ).to_be_visible()
            page.get_by_role("button", name="Request human assistance").click()
            expect(page.locator(".status-chip")).to_have_text("escalated")
            logout()
            login("test-coordinator")
            page.get_by_role("link", name="Coordinator workspace", exact=False).click()
            page.get_by_label("Queue").select_option("unassigned")
            page.get_by_role("button", name="Claim case with confirmation").click()
            expect(page.get_by_text("No cases in this queue.")).to_be_visible()
            page.get_by_label("Queue").select_option("cases")
            page.get_by_role("link", name="Open authorized case").click()
            page.get_by_label("Review / activity note").fill(
                "Synthetic checklist assistance review only"
            )
            page.get_by_role("button", name="Accept for assistance checklist").click()
            expect(
                page.get_by_text(
                    "accepted for assistance checklist · technically readable", exact=True
                )
            ).to_be_visible()
            page.get_by_label("Review / activity note").fill(
                "Synthetic referral assistance recorded"
            )
            page.get_by_role("button", name="Resolve with note").click()
            expect(page.locator(".status-chip")).to_have_text("documents pending")
            for stage in ("ready_for_human_review", "assistance_in_progress"):
                page.get_by_label("Assistance stage").select_option(stage)
                page.get_by_role("button", name="Update internal stage").click()
                expect(page.locator(".status-chip")).to_have_text(stage.replace("_", " "))
            page.get_by_label("Follow-up date and time (your local time)").fill("2099-01-01T12:00")
            page.get_by_role("button", name="Schedule in-app follow-up").click()
            expect(page.get_by_text("manual ·", exact=False).first).to_be_visible()
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, deliver()).result()
            logout()
            login("test-citizen")
            page.get_by_role("link", name="Open authorized case").click()
            expect(page.get_by_role("button", name="Acknowledge", exact=True)).to_be_visible()
            page.get_by_role("button", name="Acknowledge", exact=True).click()
            expect(page.get_by_role("button", name="Acknowledged", exact=True)).to_be_disabled()
            page.get_by_role("button", name="What documents do I still need?").click()
            expect(
                page.get_by_text("A coordinator can review the assistance task.", exact=True)
            ).to_be_visible()
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ROOT / ".tools/phase3-case-mobile.png"), full_page=True)
            assert errors == [], errors
            browser.close()
        print("PASS: sign-in, owned case creation, private PDF upload, coordinator claim/review,")
        print("referral resolution, stage updates, durable reminder delivery/acknowledgement,")
        print("record-grounded case assistant, mobile width; 0 JavaScript page errors.")
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=15)
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
