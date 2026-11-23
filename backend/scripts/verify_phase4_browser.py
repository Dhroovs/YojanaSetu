"""Real Chrome, FastAPI and Mongo workflow; synthetic users in a disposable database."""

import asyncio
import os
import secrets
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright
from pymongo import AsyncMongoClient

from app.auth import hash_password
from app.cases.models import now_utc
from app.config import Settings
from scripts.verify_browser import wait_for

ROOT = Path(__file__).resolve().parents[2]


def main():
    settings = Settings()
    database = "yojanasetu_phase4_browser_" + uuid4().hex
    password = secrets.token_urlsafe(24)
    slot = (now_utc() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
    local = slot.astimezone().strftime("%Y-%m-%dT%H:%M")
    local_end = (slot + timedelta(hours=1)).astimezone().strftime("%Y-%m-%dT%H:%M")

    async def setup():
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
            for role in ["citizen", "worker", "coordinator", "admin"]:
                await mongo[database].users.insert_one(
                    {
                        "id": "test-" + role,
                        "username": "test-" + role,
                        "role": role,
                        "active": True,
                        "password_hash": hash_password(password),
                    }
                )

    async def make_due(booking_id):
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
            await mongo[database].seva_requests.update_one(
                {"id": booking_id},
                {
                    "$set": {
                        "appointment.start": now_utc() - timedelta(minutes=5),
                        "appointment.end": now_utc() + timedelta(minutes=55),
                    }
                },
            )

    async def cleanup():
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
            await mongo.drop_database(database)

    asyncio.run(setup())
    env = dict(
        os.environ,
        MONGODB_DATABASE=database,
        MONGODB_URI=settings.mongodb_uri,
        APP_ENV="development",
        ENABLE_DEMO_DATA="false",
        ENABLE_AI="false",
        LLM_PROVIDER="none",
        ALLOW_HOSTED_LLM="false",
        VITE_API_BASE_URL="http://127.0.0.1:8004/api",
        CORS_ORIGINS='["http://localhost:5177"]',
    )
    processes, errors = [], []
    try:
        commands = [
            (
                [
                    str(ROOT / "backend/.venv/Scripts/python.exe"),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8004",
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
                    "5177",
                    "--strictPort",
                ],
                ROOT / "frontend",
            ),
        ]
        for command, cwd in commands:
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
        wait_for("http://127.0.0.1:8004/api/health")
        wait_for("http://localhost:5177")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get(
                    "CHROME_BINARY", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                ),
                headless=True,
            )
            page = browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("dialog", lambda dialog: dialog.accept())

            def login(role):
                page.goto("http://localhost:5177/login")
                page.get_by_label("Account alias").fill("test-" + role)
                page.get_by_label("Password", exact=True).fill(password)
                page.get_by_role("button", name="Sign in securely").click()
                expect(
                    page.get_by_role("heading", name="My private assistance cases")
                ).to_be_visible()
                page.get_by_role("link", name="SevaSetu", exact=True).click()

            def open_visit():
                page.get_by_role("link", name="Open visit request").click()
                expect(page.get_by_role("heading", name="Booking details")).to_be_visible()

            login("worker")
            page.get_by_role("link", name="My worker profile").click()
            page.get_by_label("Display name", exact=True).fill("Synthetic browser worker")
            page.get_by_label("Service districts (comma-separated)").fill("Test District")
            page.get_by_role("group", name="Service categories").get_by_label(
                "Document checklist help"
            ).check()
            page.get_by_role("group", name="Languages", exact=True).get_by_label(
                "en", exact=True
            ).check()
            page.get_by_role("button", name="Submit profile for internal verification").click()
            expect(page.get_by_role("heading", name="Synthetic browser worker")).to_be_visible()
            page.get_by_label("Available start (local time)").fill(local)
            page.get_by_label("Available end (up to 4 hours)").fill(local_end)
            page.get_by_role("button", name="Add declared availability window").click()
            expect(
                page.get_by_role("button", name="Add declared availability window")
            ).to_be_enabled()

            login("admin")
            page.get_by_role("link", name="Worker verification & availability").click()
            page.get_by_label("Verification review note").fill("Synthetic internal review only")
            page.get_by_label("Verification expiry (local time)").fill("2099-01-01T12:00")
            page.get_by_label("I confirm this internal verification review.").check()
            page.get_by_role("button", name="verified internally", exact=True).click()
            expect(
                page.locator("article").get_by_text("verified internally", exact=False).first
            ).to_be_visible()

            login("citizen")
            page.get_by_role("link", name="Request doorstep assistance", exact=True).click()
            page.get_by_label("Assistance category").select_option("document_assistance")
            page.get_by_label("What help is needed?").fill("Synthetic checklist guidance")
            page.get_by_label("Preferred start (your local time)").fill(local)
            page.get_by_label("Preferred end").fill(local_end)
            for label, value in [
                ("district", "Test District"),
                ("mandal", "Test Mandal"),
                ("village", "Test Village"),
            ]:
                page.get_by_label(label, exact=True).fill(value)
            page.get_by_label("Address details for the assigned worker").fill("Synthetic house 42")
            page.get_by_label("I consent to sharing necessary booking").check()
            page.get_by_role("button", name="Submit doorstep request").click()
            expect(page.locator(".status-chip")).to_have_text("pending coordinator review")
            booking_id = page.url.rsplit("/", 1)[-1]
            page.get_by_role("button", name="Get grounded coordination guidance").click()
            expect(
                page.get_by_text(
                    "Coordinator approval and worker acceptance are required.", exact=False
                ).first
            ).to_be_visible()
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ROOT / ".tools/phase4-citizen-mobile.png"), full_page=True)
            page.set_viewport_size({"width": 1280, "height": 900})

            login("coordinator")
            page.get_by_label("Show minimal unclaimed request queue").check()
            page.get_by_role("button", name="Claim request with confirmation").click()
            open_visit()
            page.get_by_role("button", name="Approve for internal assignment").click()
            expect(page.locator(".status-chip")).to_have_text("approved for assignment")
            page.get_by_role("button", name="Get grounded coordination guidance").click()
            page.get_by_label("Choose eligible worker").select_option("test-worker")
            page.get_by_label("I explicitly confirm this cancellation").check()
            page.get_by_role("button", name="Confirm assignment proposal").click()
            expect(page.locator(".status-chip")).to_have_text("worker assigned")

            login("worker")
            open_visit()
            expect(page.get_by_text("Available after assignment acceptance")).to_be_visible()
            page.get_by_role("button", name="Accept proposed assignment").click()
            expect(page.locator(".status-chip")).to_have_text("visit scheduled")
            expect(page.get_by_text("Synthetic house 42", exact=True)).to_be_visible()
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, make_due(booking_id)).result()
            page.get_by_role("button", name="Check in", exact=True).click()
            expect(page.locator(".status-chip")).to_have_text("visit in progress")
            page.get_by_label("Visit / review / problem note").fill("Synthetic guidance delivered")
            page.get_by_label("Tasks actually performed").fill(
                "Explained synthetic document checklist"
            )
            page.get_by_role("group", name="Services actually performed").get_by_label(
                "Document checklist help"
            ).check()
            page.get_by_role("button", name="Submit performed-service outcome for review").click()
            expect(page.locator(".status-chip")).to_have_text("completion pending review")

            login("coordinator")
            open_visit()
            page.get_by_label("Visit / review / problem note").fill("Synthetic outcome reviewed")
            page.get_by_label("I explicitly confirm this cancellation").check()
            page.get_by_role("button", name="Confirm reviewed visit completion").click()
            expect(page.locator(".status-chip")).to_have_text("visit completed")
            login("citizen")
            open_visit()
            page.get_by_label("Visit / review / problem note").fill("Synthetic positive feedback")
            page.get_by_role("button", name="Save feedback for reviewed visit").click()
            expect(
                page.get_by_text("Synthetic positive feedback", exact=True).first
            ).to_be_visible()
            page.goto("http://localhost:5177/seva/requests/" + booking_id)
            expect(page.get_by_role("heading", name="Private assistance workspace")).to_be_visible()
            assert errors == [], errors
            browser.close()
        print("PASS: citizen booking, read-only agent, mobile width, worker profile/calendar,")
        print(
            "admin verification, coordinator claim/approve/assign, worker accept/check-in/outcome,"
        )
        print(
            "human completion review, feedback, unauthorized UI denial; 0 JavaScript page errors."
        )
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=15)
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
