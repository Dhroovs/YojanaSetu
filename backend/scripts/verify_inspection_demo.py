"""Verify and screenshot the running local synthetic demo; never print credentials."""

import json
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from scripts.local_demo import API, MANIFEST, ROOT, WEB, call, read_access


def main():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["synthetic_only"] and manifest["seeded"]
    accounts = read_access()
    output = ROOT / "docs" / "demo-evidence"
    output.mkdir(parents=True, exist_ok=True)
    api_checks = []
    screenshots = []
    with httpx.Client(timeout=100, trust_env=False) as client:
        assert client.get(API + "/ready").status_code == 200
        assert client.get(API + "/cases").status_code == 401
        api_checks.extend(["backend readiness", "anonymous private-case denial"])
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True,
        )
        errors = []

        def snapshot(page, name):
            expect(page.locator("h1").first).to_be_visible()
            page.screenshot(path=str(output / (name + ".png")), full_page=True)
            screenshots.append(name)

        context = browser.new_context(viewport={"width": 1365, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(WEB)
        snapshot(page, "01-homepage")
        page.goto(WEB + "/login")
        snapshot(page, "02-citizen-login")
        context.close()

        for alias in ("demo-citizen", "demo-coordinator", "demo-worker", "demo-admin"):
            context = browser.new_context(viewport={"width": 1365, "height": 900})
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(WEB + "/login")
            page.get_by_label("Account alias", exact=True).fill(alias)
            page.get_by_label("Password", exact=True).fill(accounts[alias])
            with page.expect_response(lambda r: r.url.endswith("/auth/login")) as login:
                page.get_by_role("button", name="Sign in securely").click()
            assert login.value.status == 200
            token = login.value.json()["access_token"]
            expect(page.get_by_role("heading", name="My private assistance cases")).to_be_visible()

            def route(path):
                page.get_by_role("link", name="My account", exact=True).click()
                # Router navigation preserves memory-only bearer sessions.
                page.evaluate(
                    "path => { history.pushState({}, '', path);"
                    "window.dispatchEvent(new PopStateEvent('popstate')); }",
                    path,
                )

            if alias == "demo-citizen":
                snapshot(page, "03-citizen-dashboard")
                page.get_by_role("link", name="Scheme assistant", exact=True).click()
                page.get_by_label("Your question").fill(
                    "PMSBY accident insurance enrolment assistance"
                )
                page.get_by_role("button", name="Find relevant schemes").click()
                expect(page.get_by_text("evidence-only RAG (no LLM)")).to_be_visible(timeout=60000)
                expect(
                    page.get_by_role("heading", name="Pradhan Mantri Suraksha Bima Yojana (PMSBY)")
                ).to_be_visible()
                snapshot(page, "04-scheme-matcher")
                route("/my-cases/" + manifest["case_id"])
                expect(
                    page.get_by_role("heading", name="Document assistance checklist")
                ).to_be_visible()
                snapshot(page, "05-document-assistance")
                expect(page.get_by_role("heading", name="Case activity timeline")).to_be_visible()
                snapshot(page, "06-case-tracking")
                with httpx.Client(timeout=30, trust_env=False) as client:
                    case = call(client, "GET", "/cases/" + manifest["case_id"], token)
                    assert case["documents"] and case["reminders"] and case["escalations"]
                    assert any(f["status"] == "delivered" for f in case["followups"])
                    assert (
                        client.get(
                            API + "/admin/users", headers={"Authorization": "Bearer " + token}
                        ).status_code
                        == 403
                    )
                api_checks.extend(
                    [
                        "real uploaded PDF persisted",
                        "background reminder delivered",
                        "human escalation persisted",
                        "citizen admin denial",
                    ]
                )
                page.get_by_role("link", name="SevaSetu", exact=True).click()
                page.get_by_role("link", name="Request doorstep assistance", exact=True).click()
                snapshot(page, "07-sevasetu-booking")
                route("/seva/requests/" + manifest["visit_id"])
                expect(page.locator(".status-chip")).to_have_text("visit scheduled")
                snapshot(page, "08-appointment-tracking")
                if manifest.get("completed_visit_id"):
                    route("/seva/requests/" + manifest["completed_visit_id"])
                    expect(page.locator(".status-chip")).to_have_text("visit completed")
                    expect(
                        page.get_by_role("heading", name="Recorded visit outcome")
                    ).to_be_visible()
                    snapshot(page, "16-reviewed-completion")
            elif alias == "demo-coordinator":
                route("/coordinator")
                expect(
                    page.get_by_role("heading", name="Coordinator assistance queue")
                ).to_be_visible()
                snapshot(page, "09-coordinator-dashboard")
                route("/seva")
                expect(page.get_by_role("link", name="Open visit request").first).to_be_visible()
                snapshot(page, "10-coordinator-visits")
            elif alias == "demo-worker":
                page.get_by_role("link", name="SevaSetu", exact=True).click()
                expect(page.get_by_role("link", name="Open visit request").first).to_be_visible()
                snapshot(page, "11-worker-dashboard")
                page.get_by_role("link", name="My worker profile").click()
                expect(page.get_by_role("heading", name="Synthetic demo-worker")).to_be_visible()
                snapshot(page, "12-worker-calendar")
                with httpx.Client(timeout=30, trust_env=False) as client:
                    response = client.get(
                        API + "/cases/" + manifest["case_id"],
                        headers={"Authorization": "Bearer " + token},
                    )
                    assert response.status_code == 404
                api_checks.append("visit assignment does not grant private-case access")
            else:
                route("/admin")
                expect(page.get_by_role("heading", name="Operational status")).to_be_visible()
                expect(page.get_by_role("heading", name="demo-citizen", exact=True)).to_be_visible()
                assert "password_hash" not in page.locator("main").inner_text()
                form = page.locator("form").filter(
                    has=page.get_by_role("heading", name="demo-unverified", exact=True)
                )
                form.get_by_label("Account review note").fill(
                    "Synthetic administrative audit demonstration"
                )
                form.get_by_label("I confirm this account change").check()
                with page.expect_response(
                    lambda r: r.url.endswith("/admin/users/demo-unverified")
                ) as change:
                    form.get_by_role("button", name="Save account change").click()
                assert change.value.status == 200
                snapshot(page, "13-administrator-dashboard")
                route("/seva/workers")
                expect(
                    page.get_by_role("heading", name="Worker verification & workload")
                ).to_be_visible()
                snapshot(page, "14-worker-verification")
                route("/sources")
                expect(page.get_by_role("heading", name="Official source coverage")).to_be_visible()
                expect(page.get_by_role("link", name="Read official source")).to_have_count(4)
                snapshot(page, "15-source-provenance")
                api_checks.extend(
                    ["administrator user change persisted", "safe operations projection"]
                )
            with httpx.Client(timeout=30, trust_env=False) as client:
                call(client, "POST", "/auth/logout", token)
                assert (
                    client.get(
                        API + "/auth/me", headers={"Authorization": "Bearer " + token}
                    ).status_code
                    == 401
                )
            context.close()
        assert errors == [], errors
        browser.close()
    report = {
        "status": "Verified Working",
        "synthetic_only": True,
        "screenshots": screenshots,
        "api_checks": api_checks,
        "javascript_errors": errors,
        "frontend": WEB,
        "api_docs": API[:-4] + "/docs",
    }
    Path(ROOT / "artifacts" / "inspection-demo-report.json").write_text(
        json.dumps(report, indent=2)
    )
    print(f"PASS: {len(screenshots)} synthetic screenshots; role login/logout, admin mutation,")
    print("private-case isolation, live reminder delivery and real RAG; 0 JavaScript errors.")


if __name__ == "__main__":
    main()
