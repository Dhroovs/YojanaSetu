"""Registration, localization, speech fallback and five-agent citizen scenario with actual RAG."""

import asyncio
import os
import secrets
import subprocess
from pathlib import Path
from uuid import uuid4

import pymupdf
from playwright.sync_api import expect, sync_playwright
from pymongo import AsyncMongoClient

from app.config import Settings
from scripts.verify_browser import wait_for

ROOT = Path(__file__).resolve().parents[2]


def main():
    settings = Settings()
    database = "yojanasetu_phase5_browser_" + uuid4().hex
    password = secrets.token_urlsafe(24)

    async def setup():
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
            for name in ("schemes", "ai_sources"):
                query = (
                    {"is_demo": False} if name == "schemes" else {"verification_status": "verified"}
                )
                rows = (
                    await mongo[settings.mongodb_database][name]
                    .find(query, {"_id": 0})
                    .to_list(100)
                )
                assert rows, "Review and ingest official sources first."
                await mongo[database][name].insert_many(rows)

    async def cleanup():
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
            await mongo.drop_database(database)

    asyncio.run(setup())
    env = dict(
        os.environ,
        APP_ENV="production",
        MONGODB_DATABASE=database,
        MONGODB_URI=settings.mongodb_uri,
        ENABLE_AI="true",
        ENABLE_DEMO_DATA="false",
        ENABLE_CITIZEN_REGISTRATION="true",
        ENABLE_DEV_CASE_ACCESS="false",
        LLM_PROVIDER="none",
        ALLOW_HOSTED_LLM="false",
        CHROMA_PATH=str(Path(settings.chroma_path).resolve()),
        DOCUMENT_STORAGE_PATH=str(ROOT / ".tools" / database),
        VITE_API_BASE_URL="http://127.0.0.1:8005/api",
        CORS_ORIGINS='["http://localhost:5178"]',
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
                    "8005",
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
                    "5178",
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
        wait_for("http://127.0.0.1:8005/api/ready")
        wait_for("http://localhost:5178")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get(
                    "CHROME_BINARY", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                ),
                headless=True,
            )
            page = browser.new_page()
            page.add_init_script(
                "Object.defineProperty(window, 'SpeechRecognition', {value: undefined}); "
                "Object.defineProperty(window, 'webkitSpeechRecognition', {value: undefined});"
            )
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://localhost:5178/register")
            language = page.get_by_test_id("language-switcher")
            language.select_option("hi")
            expect(page.get_by_label("खाता उपनाम", exact=True)).to_be_visible()
            language.select_option("te")
            expect(page.get_by_label("ఖాతా మారుపేరు", exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_label("ఖాతా మారుపేరు", exact=True)).to_be_visible()
            language.select_option("en")
            page.get_by_label("Account alias", exact=True).fill("release-citizen")
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_label("Confirm password", exact=True).fill(password)
            page.get_by_label("I understand this service stores my assistance records").check()
            page.get_by_role("button", name="Create citizen account").click()
            expect(page.get_by_role("button", name="Sign in securely")).to_be_visible()
            page.get_by_label("Account alias", exact=True).fill("release-citizen")
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_role("button", name="Sign in securely").click()
            expect(page.get_by_role("heading", name="My private assistance cases")).to_be_visible()
            page.get_by_role("link", name="Scheme assistant", exact=True).click()
            expect(
                page.get_by_text("Speech recognition is unavailable", exact=False)
            ).to_be_visible()
            expect(page.get_by_role("button", name="Start recording")).to_be_disabled()
            expect(page.get_by_label("Local development token")).to_have_count(0)
            page.get_by_label("Your question").fill("PMSBY accident insurance enrolment assistance")
            page.get_by_role("button", name="Find relevant schemes").click()
            expect(page.get_by_text("evidence-only RAG (no LLM)")).to_be_visible(timeout=60000)
            expect(
                page.get_by_role("heading", name="Pradhan Mantri Suraksha Bima Yojana (PMSBY)")
            ).to_be_visible()
            page.get_by_role("link", name="Discover", exact=True).click()
            page.get_by_label("Source type").select_option("verified")
            expect(page.get_by_role("article")).to_have_count(3)
            language.select_option("hi")
            expect(page.get_by_label("स्रोत का प्रकार")).to_be_visible()
            language.select_option("te")
            expect(page.get_by_label("మూలం రకం")).to_be_visible()
            language.select_option("en")
            page.get_by_role("link", name="My assistance", exact=True).click()
            expect(page.get_by_role("heading", name="My private assistance cases")).to_be_visible()
            page.get_by_test_id("language-switcher").select_option("en")
            page.get_by_label("Scheme").select_option("pmsby")
            page.get_by_role("button", name="Create my case").click()
            expect(page.get_by_role("heading", name="pmsby", exact=True)).to_be_visible()
            page.get_by_label("Checklist item").select_option(index=1)
            with pymupdf.open() as pdf:
                pdf.new_page().insert_text((60, 60), "SYNTHETIC TEST DOCUMENT - no identity data")
                content = pdf.tobytes()
            page.get_by_label("Synthetic or redacted file").set_input_files(
                {"name": "synthetic.pdf", "mimeType": "application/pdf", "buffer": content}
            )
            page.get_by_role("button", name="Upload securely / retry").click()
            expect(page.get_by_text("needs human review", exact=False).first).to_be_visible()
            for label, node in [
                ("What documents do I still need?", "document_verifier"),
                ("When is my next follow-up?", "follow_up"),
                ("Request human assistance", "escalation"),
            ]:
                with page.expect_response(lambda r: r.url.endswith("/assist")) as response:
                    page.get_by_role("button", name=label, exact=True).click()
                body = response.value.json()
                assert node in body["trace"], body
            page.get_by_label("Ask about this authorized case").fill(
                "Which schemes might help with PMSBY?"
            )
            with page.expect_response(lambda r: r.url.endswith("/assist")) as response:
                page.get_by_role("button", name="Ask case assistant", exact=True).click()
            assert "scheme_matcher" in response.value.json()["trace"]
            page.get_by_role(
                "link", name="Request consent-based doorstep help for this case", exact=False
            ).click()
            expect(page.get_by_label("My related case reference (optional)")).not_to_have_value("")
            language.select_option("hi")
            expect(page.get_by_label("किस सहायता की आवश्यकता है?")).to_be_visible()
            language.select_option("te")
            expect(page.get_by_label("ఏ సహాయం కావాలి?")).to_be_visible()
            language.select_option("en")
            page.get_by_label("Assistance category").select_option("document_assistance")
            page.get_by_label("What help is needed?").fill("Synthetic doorstep document guidance")
            page.get_by_label("Preferred start (your local time)").fill("2099-01-01T12:00")
            page.get_by_label("Preferred end").fill("2099-01-01T13:00")
            for label in ("district", "mandal", "village"):
                page.get_by_label(label, exact=True).fill("Synthetic area")
            page.get_by_label("Address details for the assigned worker").fill(
                "Synthetic location 42"
            )
            page.get_by_label("I consent to sharing necessary booking").check()
            page.get_by_role("button", name="Submit doorstep request").click()
            expect(page.locator(".status-chip")).to_have_text("pending coordinator review")
            with page.expect_response(lambda r: r.url.endswith("/agent")) as response:
                page.get_by_role("button", name="Get grounded coordination guidance").click()
            body = response.value.json()
            assert body["applied"] is False and "load_authorized_context" in body["trace"]
            page.set_viewport_size({"width": 390, "height": 844})
            for selected in ("hi", "te", "en"):
                language.select_option(selected)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.get_by_role("link", name="Skip to content", exact=True).focus()
            page.keyboard.press("Enter")
            assert page.evaluate("document.activeElement.id") == "main"
            page.screenshot(path=str(ROOT / ".tools/phase5-mobile.png"), full_page=True)
            assert errors == [], errors
            browser.close()
        print("PASS: citizen registration/login, Hindi/Telugu persistence and major forms,")
        print("voice fallback, individual-session production RAG, real PDF checklist/upload,")
        print(
            "five-agent scenario with authorized linked visit, mobile layout; 0 JavaScript errors."
        )
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=15)
        asyncio.run(cleanup())
        # Only synthetic files created in this fixture's named storage directory.
        storage = ROOT / ".tools" / database
        if storage.exists():
            for path in storage.iterdir():
                if path.is_file():
                    path.unlink()
            storage.rmdir()


if __name__ == "__main__":
    main()
