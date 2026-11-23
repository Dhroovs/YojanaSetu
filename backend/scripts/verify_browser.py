"""Real Chrome + API + Mongo smoke test; isolated DB, temporary loopback servers.

Run from backend after installing requirements-browser.txt. Set NODE_BINARY and
CHROME_BINARY if the executable locations differ. MongoDB must be running locally.
"""

import asyncio
import os
import secrets
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx
from playwright.sync_api import expect, sync_playwright
from pymongo import AsyncMongoClient

ROOT = Path(__file__).resolve().parents[2]
TOKEN = secrets.token_urlsafe(32)
DATABASE = f"yojanasetu_browser_{uuid4().hex}"
URI = os.environ.get("MONGO_TEST_URI", "mongodb://127.0.0.1:27017")


def wait_for(url):
    for _ in range(100):
        try:
            if httpx.get(url).status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Server did not become ready: {url}")


async def cleanup():
    async with AsyncMongoClient(URI, serverSelectionTimeoutMS=3000) as mongo:
        await mongo.drop_database(DATABASE)


def main():
    env = dict(
        os.environ,
        APP_ENV="development",
        MONGODB_URI=URI,
        MONGODB_DATABASE=DATABASE,
        ENABLE_DEMO_DATA="true",
        ENABLE_DEV_CASE_ACCESS="true",
        DEV_ACCESS_TOKEN=TOKEN,
        CORS_ORIGINS='["http://localhost:5174"]',
        VITE_API_BASE_URL="http://127.0.0.1:8001/api",
    )
    processes = []
    errors = []
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
                    "8001",
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
                    "5174",
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
        wait_for("http://127.0.0.1:8001/api/health")
        wait_for("http://localhost:5174")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get(
                    "CHROME_BINARY", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                ),
                headless=True,
            )
            page = browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://localhost:5174")
            expect(page.get_by_role("heading", level=1)).to_contain_text("possibilities")
            page.get_by_role("link", name="Explore demo schemes").click()
            expect(page.get_by_role("article")).to_have_count(3)
            page.get_by_label("Search by topic or category").fill("no-matching-demo-scheme")
            page.get_by_role("button", name="Search schemes").click()
            expect(page.get_by_text("No schemes found. Try another topic.")).to_be_visible()
            page.get_by_label("Search by topic or category").fill("education")
            page.get_by_role("button", name="Search schemes").click()
            expect(page.get_by_role("article")).to_have_count(1)
            page.get_by_role("link", name="Explore scheme").click()
            expect(page.get_by_role("heading", level=1)).to_have_text("Learning Pathways")
            page.get_by_label("Local development token").fill("invalid-token")
            page.get_by_role("button", name="Create demo case").click()
            expect(page.get_by_role("alert")).to_contain_text("valid local development token")
            page.get_by_label("Local development token").fill(TOKEN)
            page.get_by_role("button", name="Create demo case").click()
            expect(page.get_by_role("status")).to_contain_text("Case created")
            page.get_by_role("link", name="Track case", exact=False).last.click()
            page.get_by_label("Local development token").fill(TOKEN)
            page.get_by_role("button", name="Check status").click()
            expect(page.get_by_role("status")).to_contain_text("received")
            page.get_by_role("link", name="SevaSetu", exact=True).click()
            page.get_by_label("Demo district").fill("Demo district")
            page.get_by_label("Preferred date").fill("2099-01-01")
            page.get_by_label("Local development token").fill(TOKEN)
            page.get_by_role("button", name="Save demo request").click()
            expect(page.get_by_role("status")).to_contain_text("This does not book a visit")
            page.get_by_label("Language preview").select_option("hi")
            expect(page.get_by_role("status").first).to_contain_text("Translation is not connected")
            page.get_by_role("link", name="Coordinator workspace").click()
            expect(page.get_by_role("main")).to_contain_text("not connected")
            page.get_by_role("link", name="My assistance").click()
            expect(page.get_by_role("heading", level=1)).to_have_text("Citizen assistance")
            page.get_by_label("Language preview").select_option("te")
            expect(page.get_by_role("status")).to_contain_text("Translation is not connected")
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto("http://localhost:5174")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ROOT / ".tools/phase1-mobile.png"), full_page=True)
            assert errors == [], errors
            browser.close()
        print("PASS: home, search, details, case creation, tracking, doorstep intake,")
        print("language notice, coordinator placeholder, mobile overflow; 0 page errors")
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=15)
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
