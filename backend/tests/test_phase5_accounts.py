import os

import pytest
from test_phase3_mongo import live as live

from app.ai.models import MatchResponse, Profile

pytestmark = pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")


def test_registration_cannot_grant_roles_and_login_is_individual(live):
    c, h, _ = live
    body = {
        "username": "new-citizen",
        "password": "synthetic-registration-password",
        "consent": True,
        "language": "te",
    }
    assert c.post("/api/auth/register", json={**body, "role": "admin"}).status_code == 422
    assert c.post("/api/auth/register", json={**body, "consent": False}).status_code == 422
    response = c.post("/api/auth/register", json=body)
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "citizen" and "password" not in response.text
    assert c.post("/api/auth/register", json=body).status_code == 409
    login = c.post("/api/auth/login", json={k: body[k] for k in ("username", "password")})
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert (
        c.post("/api/auth/preferences", headers=headers, json={"language": "hi"}).status_code == 200
    )
    assert (
        c.post(
            "/api/auth/preferences", headers=headers, json={"language": "hi", "role": "admin"}
        ).status_code
        == 422
    )
    second_login = c.post("/api/auth/login", json={k: body[k] for k in ("username", "password")})
    assert second_login.json()["language"] == "hi"
    assert c.get("/api/cases", headers=headers).json()["items"] == []
    assert c.get("/api/admin/users", headers=headers).status_code == 403
    assert c.get("/api/admin/users", headers=h["admin-a"]).status_code == 200


def test_admin_changes_revoke_sessions_and_never_return_secrets(live):
    c, h, _ = live
    listing = c.get("/api/admin/users", headers=h["admin-a"])
    assert "password_hash" not in listing.text and "token_hash" not in listing.text
    body = {
        "revision": 0,
        "role": "citizen",
        "active": False,
        "confirmed": True,
        "note": "Synthetic disable review",
    }
    assert (
        c.post("/api/admin/users/citizen-b", headers=h["citizen-a"], json=body).status_code == 403
    )
    response = c.post("/api/admin/users/citizen-b", headers=h["admin-a"], json=body)
    assert response.status_code == 200, response.text
    assert c.get("/api/auth/me", headers=h["citizen-b"]).status_code == 401
    assert c.post("/api/admin/users/citizen-b", headers=h["admin-a"], json=body).status_code == 409
    assert (
        c.post(
            "/api/admin/users/admin-a", headers=h["admin-a"], json={**body, "role": "admin"}
        ).status_code
        == 409
    )
    ops = c.get("/api/admin/operations", headers=h["admin-a"])
    assert (
        ops.status_code == 200 and "mongodb_uri" not in ops.text and "model_api_key" not in ops.text
    )


def test_production_matcher_accepts_individual_login_without_development_secret(live):
    c, h, settings = live
    sessions = []

    class Matcher:
        async def match(self, body, session):
            sessions.append(session)
            return MatchResponse(
                conversation_id="a" * 43,
                profile=Profile(),
                message="No matching evidence",
                recommendations=[],
                follow_up_questions=[],
                warnings=[],
                mode="test",
                trace=[],
            )

    c.app.state.ai_service = Matcher()
    settings.enable_ai = True
    settings.app_env = "production"
    headers = {**h["citizen-a"], "X-Session-Key": "x" * 32}
    assert (
        c.post(
            "/api/ai/scheme-match", headers=headers, json={"question": "What support is available?"}
        ).status_code
        == 200
    )
    assert sessions[0] != "x" * 32
    assert (
        c.post(
            "/api/ai/scheme-match",
            headers={"X-Session-Key": "x" * 32},
            json={"question": "What support?"},
        ).status_code
        == 403
    )
    assert (
        c.post(
            "/api/ai/scheme-match",
            headers={**headers, "Authorization": "Bearer invalid"},
            json={"question": "What support?"},
        ).status_code
        == 401
    )
