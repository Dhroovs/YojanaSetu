"""Chrome smoke test against actual ingested sources, local ONNX, Mongo and React.

No LLM is enabled. Uses temporary ports 5175/8002 and cleans up only its own
conversation records. The configured official knowledge base is read, not replaced.
"""

import asyncio
import hashlib
import os
import secrets
import subprocess
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from pymongo import AsyncMongoClient

from app.config import Settings
from scripts.verify_browser import wait_for

ROOT = Path(__file__).resolve().parents[2]


def main():
    settings = Settings()
    token = secrets.token_urlsafe(32)
    env = dict(
        os.environ,
        APP_ENV="development",
        ENABLE_AI="true",
        ENABLE_DEV_CASE_ACCESS="true",
        DEV_ACCESS_TOKEN=token,
        LLM_PROVIDER="none",
        VITE_API_BASE_URL="http://127.0.0.1:8002/api",
        CORS_ORIGINS='["http://localhost:5175"]',
    )
    processes, errors = [], []
    session_key = None

    async def cleanup():
        if session_key:
            async with AsyncMongoClient(settings.mongodb_uri) as mongo:
                await mongo[settings.mongodb_database].ai_conversations.delete_many(
                    {
                        "owner": hashlib.sha256(session_key.encode()).hexdigest(),
                    }
                )

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
                    "8002",
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
                    "5175",
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
        wait_for("http://127.0.0.1:8002/api/health")
        wait_for("http://localhost:5175")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get(
                    "CHROME_BINARY", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                ),
                headless=True,
            )
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))

            def capture(request):
                nonlocal session_key
                if "/api/ai/scheme-" in request.url:
                    session_key = request.headers.get("x-session-key") or session_key

            page.on("request", capture)
            page.goto("http://localhost:5175/assistant")
            page.get_by_label("Local development token").fill(token)
            page.get_by_label("Your question").fill(
                "I am a farmer from Telangana. What PM KISAN support might help?"
            )
            page.get_by_role("button", name="Find relevant schemes").click()
            expect(page.get_by_text("evidence-only RAG (no LLM)")).to_be_visible(timeout=60000)
            expect(page.get_by_text("Unable to determine", exact=True).first).to_be_visible()
            expect(page.get_by_text("Source may be outdated.", exact=False)).to_be_visible()
            page.locator(".citation summary").first.click()
            expect(page.get_by_role("link", name="Read official source").first).to_have_attribute(
                "href", "https://pmkisan.gov.in/"
            )
            page.get_by_label("Your question").fill("I am 55 years old")
            page.get_by_role("button", name="Ask follow-up").click()
            expect(page.get_by_role("button", name="Ask follow-up")).to_be_enabled(timeout=60000)
            page.get_by_text("Optional profile", exact=False).click()
            expect(page.get_by_label("Age", exact=True)).to_have_value("55")
            expect(page.get_by_label("State of residence")).to_have_value("Telangana")
            page.get_by_role("link", name="My assistance").click()
            expect(page.get_by_text("Matches from this session")).to_be_visible()
            expect(
                page.get_by_role("heading", name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)")
            ).to_be_visible()
            page.get_by_role("link", name="Discover", exact=True).click()
            page.get_by_label("Source type").select_option("verified")
            expect(page.get_by_role("article")).to_have_count(3)
            page.get_by_role("article").filter(
                has=page.get_by_role("heading", name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)")
            ).get_by_role("link", name="Explore scheme").click()
            expect(
                page.get_by_role("heading", name="Official sources & verification")
            ).to_be_visible()
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto("http://localhost:5175/assistant")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ROOT / ".tools/phase2-assistant-mobile.png"), full_page=True)
            assert errors == [], errors
            browser.close()
        print("PASS: real-source assistant, citations, stale warning, follow-up memory, dashboard,")
        print("verified-only discovery, source details, mobile width; 0 JavaScript page errors.")
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=15)
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
