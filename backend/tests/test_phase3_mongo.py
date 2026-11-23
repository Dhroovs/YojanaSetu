"""Real persistence and authorization tests with isolated synthetic fixtures."""

import asyncio
import os
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient
from test_phase3 import synthetic_pdf

from app.auth import hash_password
from app.cases.automation import process_due, purge_expired
from app.cases.models import now_utc
from app.cases.runtime import PrivateRuntime
from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.skipif(
    not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI for Phase 3 Mongo tests"
)
PASSWORD = "synthetic-password-for-isolated-tests"


@pytest.fixture
def live(tmp_path):
    uri, name = os.environ["MONGO_TEST_URI"], "yojanasetu_phase3_test_" + uuid4().hex
    settings = Settings(
        _env_file=None,
        mongodb_uri=uri,
        mongodb_database=name,
        enable_demo_data=True,
        enable_dev_case_access=True,
        dev_access_token="legacy-development-only-test-token-123456",
        login_attempts_per_minute=100,
        document_storage_path=str(tmp_path / "files"),
        document_max_bytes=1_000_000,
    )

    async def prepare():
        async with AsyncMongoClient(uri, tz_aware=True) as mongo:
            db = mongo[name]
            for alias, role in [
                ("citizen-a", "citizen"),
                ("citizen-b", "citizen"),
                ("worker-a", "worker"),
                ("coord-a", "coordinator"),
                ("coord-b", "coordinator"),
                ("admin-a", "admin"),
            ]:
                await db.users.insert_one(
                    {
                        "id": alias,
                        "username": alias,
                        "role": role,
                        "active": True,
                        "password_hash": hash_password(PASSWORD),
                    }
                )
            await db.schemes.insert_one(
                {
                    "id": "test-source-scheme",
                    "title": "Synthetic test-only checklist",
                    "category": "Synthetic testing",
                    "summary": "Not government data",
                    "is_demo": False,
                    "documents": ["Synthetic household record"],
                    "eligibility": [],
                    "guidance": [],
                    "source_references": ["test-only-source"],
                }
            )
            await db.ai_sources.insert_one(
                {
                    "source_id": "test-only-source",
                    "verification_status": "verified",
                    "index_version": "test-version-1",
                    "required_documents": ["Synthetic household record"],
                    "field_evidence": {
                        "required_documents": "Synthetic fixture, isolated DB only."
                    },
                }
            )

    async def cleanup():
        async with AsyncMongoClient(uri) as mongo:
            await mongo.drop_database(name)

    asyncio.run(prepare())
    app = create_app(settings)
    try:
        with TestClient(app) as client:
            headers = {}
            for alias in ("citizen-a", "citizen-b", "worker-a", "coord-a", "coord-b", "admin-a"):
                response = client.post(
                    "/api/auth/login", json={"username": alias, "password": PASSWORD}
                )
                assert response.status_code == 200, response.text
                headers[alias] = {"Authorization": "Bearer " + response.json()["access_token"]}
            yield client, headers, settings
    finally:
        asyncio.run(cleanup())


def create_case(client, headers, key=None):
    response = client.post(
        "/api/cases",
        headers={**headers, "Idempotency-Key": key or str(uuid4())},
        json={"scheme_id": "test-source-scheme", "assistance_type": "Synthetic assistance"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def change(client, headers, case, path, payload, key=None):
    return client.post(
        f"/api/cases/{case['id']}{path}",
        headers={**headers, "Idempotency-Key": key or str(uuid4())},
        json={"revision": case["revision"], **payload},
    )


def claim(client, headers, case):
    response = change(
        client,
        headers,
        case,
        "/assignment",
        {
            "coordinator_id": "coord-a",
            "worker_ids": [],
            "confirmed": True,
            "note": "Synthetic coordinator self-claim",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def upload(client, headers, case, data=None):
    response = client.post(
        f"/api/cases/{case['id']}/documents?item_id={case['checklist'][0]['id']}&revision={case['revision']}",
        headers={**headers, "Content-Type": "application/pdf", "Idempotency-Key": str(uuid4())},
        content=data or synthetic_pdf(),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_auth_sessions_owner_enforcement_and_legacy_isolation(live):
    client, headers, settings = live
    assert client.get("/api/cases").status_code == 401
    case = create_case(client, headers["citizen-a"])
    assert case["owner_id"] == "citizen-a" and case["checklist_verified"]
    assert "creation_key" not in case and "operations" not in case
    assert client.get(f"/api/cases/{case['id']}", headers=headers["citizen-b"]).status_code == 404
    assert client.get(f"/api/cases/{case['id']}", headers=headers["worker-a"]).status_code == 404
    assert (
        client.get(
            f"/api/cases/{case['id']}", headers={"X-Dev-Token": settings.dev_access_token}
        ).status_code
        == 404
    )
    assert client.get("/api/cases", headers=headers["citizen-b"]).json()["items"] == []
    assert client.get("/api/coordinator/queue", headers=headers["citizen-a"]).status_code == 403
    assert (
        client.post(
            "/api/auth/login", json={"username": "citizen-a", "password": "not-the-password"}
        ).status_code
        == 401
    )
    assert client.post("/api/auth/logout", headers=headers["citizen-a"]).status_code == 204
    assert client.get("/api/auth/me", headers=headers["citizen-a"]).status_code == 401
    assert client.get("/api/cases?page=0", headers=headers["admin-a"]).status_code == 422


def test_claim_private_upload_human_review_and_stage_transitions(live):
    client, h, _ = live
    case = create_case(client, h["citizen-a"])
    unassigned = client.get("/api/coordinator/queue?kind=unassigned", headers=h["coord-a"]).json()[
        "items"
    ]
    assert unassigned[0]["id"] == case["id"]
    assert "owner_id" not in unassigned[0] and "documents" not in unassigned[0]
    case = claim(client, h["coord-a"], case)
    case = upload(client, h["citizen-a"], case)
    document = case["documents"][0]
    assert document["technical_status"] == "technically_readable"
    assert document["review_status"] == "needs_human_review" and "storage_key" not in document
    file_url = f"/api/cases/{case['id']}/documents/{document['id']}/content"
    assert client.get(file_url, headers=h["citizen-b"]).status_code == 404
    assert client.get(file_url).status_code == 401
    file_response = client.get(file_url, headers=h["citizen-a"])
    assert (
        file_response.status_code == 200
        and "attachment" in file_response.headers["content-disposition"]
    )
    assert file_response.headers["cache-control"] == "no-store"
    review = {
        "status": "accepted_for_assistance_checklist",
        "note": "Synthetic checklist acceptance only",
    }
    assert (
        change(
            client, h["citizen-a"], case, f"/documents/{document['id']}/review", review
        ).status_code
        == 403
    )
    assert (
        change(
            client, h["coord-b"], case, f"/documents/{document['id']}/review", review
        ).status_code
        == 404
    )
    response = change(client, h["coord-a"], case, f"/documents/{document['id']}/review", review)
    assert response.status_code == 200, response.text
    case = response.json()
    assert case["stage"] == "ready_for_human_review"
    stale = change(
        client,
        h["coord-a"],
        {**case, "revision": 0},
        "/stage",
        {"stage": "assistance_in_progress", "note": "Test"},
    )
    assert stale.status_code == 409
    for stage in ("assistance_in_progress", "waiting_for_external_update", "completed"):
        response = change(
            client,
            h["coord-a"],
            case,
            "/stage",
            {"stage": stage, "note": "Internal test milestone"},
        )
        assert response.status_code == 200, response.text
        case = response.json()
    assert case["status"] == "resolved" and "No official approval" in case["disclaimer"]
    assert (
        change(
            client, h["coord-a"], case, "/stage", {"stage": "closed", "note": "Test closure"}
        ).status_code
        == 422
    )
    response = change(
        client,
        h["coord-a"],
        case,
        "/stage",
        {"stage": "closed", "note": "Test closure", "confirmed": True},
    )
    assert response.status_code == 200, response.text


def test_idempotency_duplicates_upload_validation_and_worker_permissions(live):
    client, h, _ = live
    key = str(uuid4())
    first = create_case(client, h["citizen-a"], key)
    assert create_case(client, h["citizen-a"], key)["id"] == first["id"]
    first = claim(client, h["coord-a"], first)
    data = synthetic_pdf()
    first = upload(client, h["citizen-a"], first, data)
    repeated = upload(client, h["citizen-a"], first, data)
    assert len(repeated["documents"]) == 1 and repeated["revision"] == first["revision"]
    response = change(
        client,
        h["admin-a"],
        first,
        "/assignment",
        {
            "coordinator_id": "coord-a",
            "worker_ids": ["worker-a"],
            "confirmed": True,
            "note": "Assign synthetic worker",
        },
    )
    assert response.status_code == 200, response.text
    case = response.json()
    assert client.get(f"/api/cases/{case['id']}", headers=h["worker-a"]).status_code == 200
    assert (
        change(
            client,
            h["worker-a"],
            case,
            "/stage",
            {"stage": "closed", "confirmed": True, "note": "No authority"},
        ).status_code
        == 403
    )
    invalid = client.post(
        f"/api/cases/{case['id']}/documents?item_id={case['checklist'][0]['id']}&revision={case['revision']}",
        content=b"executable",
        headers={
            **h["citizen-a"],
            "Content-Type": "application/x-msdownload",
            "Idempotency-Key": str(uuid4()),
        },
    )
    assert invalid.status_code == 415
    too_big = client.post(
        f"/api/cases/{case['id']}/documents?item_id={case['checklist'][0]['id']}&revision={case['revision']}",
        content=b"a" * 1_000_001,
        headers={
            **h["citizen-a"],
            "Content-Type": "application/pdf",
            "Idempotency-Key": str(uuid4()),
        },
    )
    assert too_big.status_code == 413


def test_agent_handoffs_escalations_ack_resolution_and_private_history(live):
    client, h, _ = live
    case = create_case(client, h["citizen-a"])
    case = claim(client, h["coord-a"], case)
    for text, node in [
        ("What documents do I still need?", "document_verifier"),
        ("When is my next follow-up?", "follow_up"),
        ("What is happening with my assistance case?", "case_status"),
    ]:
        response = change(client, h["citizen-a"], case, "/assist", {"question": text})
        assert response.status_code == 200, response.text
        assert node in response.json()["trace"]
    request = {"question": "Can I request help from a coordinator?", "apply_changes": True}
    response = change(client, h["citizen-a"], case, "/assist", request)
    assert response.status_code == 200, response.text
    case = client.get(f"/api/cases/{case['id']}", headers=h["citizen-a"]).json()
    assert case["stage"] == "escalated" and len(case["escalations"]) == 1
    response = change(client, h["citizen-a"], case, "/assist", request)
    assert response.status_code == 200, response.text
    case = client.get(f"/api/cases/{case['id']}", headers=h["citizen-a"]).json()
    assert len(case["escalations"]) == 1
    escalation = case["escalations"][0]
    for action, note in [
        ("acknowledge", "Acknowledged synthetic referral"),
        ("resolve", "Synthetic assistance completed"),
    ]:
        response = change(
            client,
            h["coord-a"],
            case,
            f"/escalations/{escalation['id']}",
            {"action": action, "note": note},
        )
        assert response.status_code == 200, response.text
        case = response.json()
    assert case["escalations"][0]["status"] == "resolved"
    assert (
        client.get(f"/api/cases/{case['id']}/activity", headers=h["citizen-b"]).status_code == 404
    )
    assert (
        client.get("/api/coordinator/queue?kind=escalations", headers=h["coord-a"]).json()["total"]
        == 0
    )


def test_scheduler_restart_notification_ack_and_retention(live):
    client, h, settings = live
    case = create_case(client, h["citizen-a"])
    case = upload(client, h["citizen-a"], case)
    noon = now_utc().replace(hour=6, minute=30, second=0, microsecond=0)

    async def sweep():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            db = mongo[settings.mongodb_database]
            await db.assistance_cases.update_one(
                {"id": case["id"]},
                {
                    "$set": {
                        "preferences.quiet_start": 0,
                        "preferences.quiet_end": 0,
                        "next_automation_at": noon,
                        "followups.0.due_at": noon,
                        "documents.0.expires_at": noon - timedelta(days=1),
                    }
                },
            )
            runtime = PrivateRuntime(db, settings)
            await runtime.initialize()
            await process_due(runtime.cases, noon)
            await process_due(runtime.cases, noon)
            await purge_expired(runtime.cases, noon)

    asyncio.run(sweep())
    # Fresh runtime/client in the worker persisted updates visible to the running API.
    case = client.get(f"/api/cases/{case['id']}", headers=h["citizen-a"]).json()
    assert len(case["reminders"]) == 1
    assert case["documents"][0]["deleted_at"] and case["documents"][0]["storage_removed"]
    document = case["documents"][0]
    assert (
        client.get(
            f"/api/cases/{case['id']}/documents/{document['id']}/content", headers=h["citizen-a"]
        ).status_code
        == 410
    )
    response = change(
        client,
        h["citizen-a"],
        case,
        f"/reminders/{case['reminders'][0]['id']}/acknowledge",
        {"note": ""},
    )
    assert response.status_code == 200, response.text
    assert "citizen-a" in response.json()["reminders"][0]["acknowledged_by"]
    assert list((__import__("pathlib").Path(settings.document_storage_path)).iterdir()) == []
