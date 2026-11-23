import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from pymongo import AsyncMongoClient
from test_phase3_mongo import live as live

from app.cases.models import now_utc
from app.seva.models import BookingInput, Slot


def window():
    start = now_utc() + timedelta(days=2)
    return {"start": start.isoformat(), "end": (start + timedelta(hours=1)).isoformat()}


def request_body(slot=None):
    return {
        "category": "document_assistance",
        "description": "Synthetic service guidance request",
        "preferred_window": slot or window(),
        "location": {
            "district": "Test District",
            "mandal": "Test Mandal",
            "village": "Test Village",
            "address": "Synthetic house 42",
        },
        "language": "en",
        "share_with_assigned_worker": True,
        "accessibility": ["reading_help"],
    }


def post(client, h, path, body, key=None):
    return client.post(
        "/api/seva" + path, json=body, headers={**h, "Idempotency-Key": key or str(uuid4())}
    )


def create(client, h, slot=None):
    response = post(client, h, "/requests", request_body(slot))
    assert response.status_code == 201, response.text
    return response.json()


def act(client, h, b, action, **kwargs):
    return post(
        client,
        h,
        f"/requests/{b['id']}/actions",
        {"action": action, "revision": b["revision"], **kwargs},
    )


def claim_approve(client, h, b):
    for action in ("claim", "approve"):
        response = act(client, h, b, action, confirmed=True)
        assert response.status_code == 200, response.text
        b = response.json()
    return b


def worker(client, h, slot):
    response = post(
        client,
        h["worker-a"],
        "/workers/worker-a",
        {
            "display_name": "Synthetic worker",
            "kind": "field_worker",
            "categories": ["document_assistance"],
            "languages": ["en"],
            "districts": ["Test District"],
            "capabilities": ["reading_help"],
            "capacity": 5,
        },
    )
    assert response.status_code == 201, response.text
    response = post(
        client,
        h["admin-a"],
        "/workers/worker-a/verification",
        {
            "revision": 0,
            "status": "verified_internally",
            "expires_at": (now_utc() + timedelta(days=30)).isoformat(),
            "confirmed": True,
            "note": "Synthetic internal review only",
        },
    )
    assert response.status_code == 200, response.text
    response = post(
        client,
        h["worker-a"],
        "/workers/worker-a/availability",
        {"revision": response.json()["revision"], "slots": [slot]},
    )
    assert response.status_code == 200, response.text


def assign(client, h, b, slot, key=None, path="assignment"):
    return post(
        client,
        h,
        f"/requests/{b['id']}/{path}",
        {
            "revision": b["revision"],
            "worker_id": "worker-a",
            "window": slot,
            "confirmed": True,
            "note": "Synthetic assignment",
        },
        key,
    )


def test_booking_validation_and_location_consent():
    body = request_body()
    body["location"].update(latitude=17.0, longitude=78.0)
    with pytest.raises(ValidationError):
        BookingInput.model_validate(body)
    body["location"]["map_consent"] = True
    assert BookingInput.model_validate(body).location.map_consent
    with pytest.raises(ValidationError):
        Slot(start=now_utc(), end=now_utc() - timedelta(hours=1))


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_booking_ownership_consent_and_admin_verification(live):
    c, h, _ = live
    b = create(c, h["citizen-a"])
    assert c.get(f"/api/seva/requests/{b['id']}", headers=h["citizen-b"]).status_code == 404
    assert c.get("/api/seva/requests", headers=h["citizen-b"]).json()["items"] == []
    assert c.get("/api/seva/requests").status_code == 401
    assert (
        post(
            c,
            h["citizen-a"],
            "/workers/worker-a/verification",
            {
                "revision": 0,
                "status": "verified_internally",
                "confirmed": True,
                "note": "Not authorized",
            },
        ).status_code
        == 403
    )
    assert c.get("/api/seva/workers", headers=h["citizen-a"]).status_code == 403
    minimal = c.get("/api/seva/requests?unassigned=true", headers=h["coord-a"]).json()["items"][0]
    assert "location" not in minimal and "description" not in minimal
    body = request_body()
    body["share_with_assigned_worker"] = False
    denied = post(c, h["citizen-a"], "/requests", body).json()
    denied = act(c, h["coord-a"], denied, "claim", confirmed=True).json()
    assert act(c, h["coord-a"], denied, "approve").status_code == 409


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_verified_assignment_acceptance_conflicts_and_cancel(live):
    c, h, _ = live
    slot = window()
    b = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    assert assign(c, h["coord-a"], b, slot).status_code == 409
    worker(c, h, slot)
    proposal = post(c, h["coord-a"], f"/requests/{b['id']}/agent", {})
    assert proposal.status_code == 422  # Empty assignment objects are not implicit approval.
    proposal = c.post(f"/api/seva/requests/{b['id']}/agent", headers=h["coord-a"])
    assert proposal.status_code == 200, proposal.text
    assert proposal.json()["applied"] is False and len(proposal.json()["candidates"]) == 1
    key = str(uuid4())
    response = assign(c, h["coord-a"], b, slot, key)
    assert response.status_code == 200, response.text
    assert assign(c, h["coord-a"], b, slot, key).status_code == 200
    b = response.json()
    assert b["stage"] == "worker_assigned" and not b["assignment_accepted"]
    pending = c.get(f"/api/seva/requests/{b['id']}", headers=h["worker-a"]).json()
    assert pending["location"]["address"] == "Available after assignment acceptance"
    assert act(c, h["citizen-a"], b, "accept").status_code == 403
    b = act(c, h["worker-a"], b, "accept").json()
    assert b["stage"] == "visit_scheduled" and b["assignment_accepted"]
    assert (
        c.get(f"/api/seva/requests/{b['id']}", headers=h["worker-a"]).json()["location"]["address"]
        == "Synthetic house 42"
    )
    second = claim_approve(c, h["coord-a"], create(c, h["citizen-b"], slot))
    assert assign(c, h["coord-a"], second, slot).status_code == 409
    cancelled = act(c, h["citizen-a"], b, "cancel", confirmed=True)
    assert cancelled.status_code == 200, cancelled.text
    assert assign(c, h["coord-a"], second, slot).status_code == 200


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_concurrent_assignments_cannot_double_book(live):
    c, h, _ = live
    slot = window()
    worker(c, h, slot)
    one = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    two = claim_approve(c, h["coord-a"], create(c, h["citizen-b"], slot))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda b: assign(c, h["coord-a"], b, slot), [one, two]))
    assert sorted(r.status_code for r in results) == [200, 409]


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_reschedule_requires_new_acceptance_and_suspension_blocks_access(live):
    c, h, settings = live
    slot = window()
    worker(c, h, slot)
    b = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    b = assign(c, h["coord-a"], b, slot).json()
    b = act(c, h["worker-a"], b, "accept").json()
    b = act(c, h["citizen-a"], b, "reschedule", confirmed=True, window=window()).json()
    assert (
        b["stage"] == "rescheduling_requested"
        and not b["assignment_accepted"]
        and b["worker_id"] is None
    )

    async def suspend():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as db:
            await db[settings.mongodb_database].seva_workers.update_one(
                {"id": "worker-a"}, {"$set": {"verification_status": "suspended", "active": False}}
            )

    asyncio.run(suspend())
    assert assign(c, h["coord-a"], b, slot).status_code == 409


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_worker_outcome_requires_coordinator_review(live):
    c, h, settings = live
    slot = window()
    worker(c, h, slot)
    b = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    b = assign(c, h["coord-a"], b, slot).json()
    b = act(c, h["worker-a"], b, "accept").json()
    assert (
        act(
            c,
            h["worker-a"],
            b,
            "submit_outcome",
            note="Synthetic service",
            services_performed=["document_assistance"],
        ).status_code
        == 409
    )

    async def due():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as db:
            await db[settings.mongodb_database].seva_requests.update_one(
                {"id": b["id"]},
                {
                    "$set": {
                        "appointment.start": now_utc() - timedelta(minutes=5),
                        "appointment.end": now_utc() + timedelta(minutes=55),
                    }
                },
            )

    asyncio.run(due())
    b = act(c, h["worker-a"], b, "check_in").json()
    assert b["stage"] == "visit_in_progress"
    b = act(
        c,
        h["worker-a"],
        b,
        "submit_outcome",
        note="Synthetic assistance provided",
        services_performed=["document_assistance"],
    ).json()
    assert b["stage"] == "completion_pending_review"
    assert (
        act(
            c, h["worker-a"], b, "confirm_completion", confirmed=True, note="No authority"
        ).status_code
        == 403
    )
    b = act(
        c,
        h["coord-a"],
        b,
        "confirm_completion",
        confirmed=True,
        note="Synthetic human outcome review",
    ).json()
    assert b["stage"] == "visit_completed"
    feedback = act(c, h["citizen-a"], b, "feedback", rating=5, note="Synthetic feedback")
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["feedback"]["rating"] == 5


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_linked_case_agent_checks_ownership_and_remains_read_only(live):
    c, h, _ = live
    case = c.post(
        "/api/cases",
        headers={**h["citizen-a"], "Idempotency-Key": str(uuid4())},
        json={"scheme_id": "test-source-scheme", "assistance_type": "Synthetic help"},
    ).json()
    body = request_body()
    body["case_id"] = case["id"]
    booking = post(c, h["citizen-a"], "/requests", body).json()
    question = {
        "revision": case["revision"],
        "question": "Plan a doorstep home visit",
        "doorstep_request_id": booking["id"],
    }
    response = c.post(f"/api/cases/{case['id']}/assist", headers=h["citizen-a"], json=question)
    assert response.status_code == 200, response.text
    assert response.json()["result"]["agent"] == "doorstep_coordinator"
    assert response.json()["applied"] is False
    assert (
        c.get(f"/api/seva/requests/{booking['id']}", headers=h["citizen-a"]).json()["revision"] == 0
    )
    assert (
        c.post(f"/api/cases/{case['id']}/assist", headers=h["citizen-b"], json=question).status_code
        == 404
    )
    question["apply_changes"] = True
    assert (
        c.post(f"/api/cases/{case['id']}/assist", headers=h["citizen-a"], json=question).status_code
        == 422
    )


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_automation_delivers_localized_notices_and_releases_unaccepted_slots(live):
    from app.cases.runtime import PrivateRuntime
    from app.seva.automation import process_due
    from app.seva.service import SevaService
    from app.seva.store import SevaStore

    c, h, settings = live
    slot = window()
    worker(c, h, slot)
    body = request_body(slot)
    body["language"] = "en"
    body["preferences"] = {"in_app": True, "quiet_start": 0, "quiet_end": 0}
    b = claim_approve(c, h["coord-a"], post(c, h["citizen-a"], "/requests", body).json())
    b = assign(c, h["coord-a"], b, slot).json()

    async def sweep():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            db = mongo[settings.mongodb_database]
            runtime = PrivateRuntime(db, settings)
            store = SevaStore(db)
            service = SevaService(store, runtime.cases, runtime.auth, settings)
            now = now_utc()
            await db.seva_requests.update_one(
                {"id": b["id"]},
                {
                    "$set": {
                        "updated_at": now - timedelta(hours=25),
                        "language": "te",
                        "next_automation_at": now - timedelta(seconds=1),
                    }
                },
            )
            assert await process_due(service, now) == 1
            result = await store.booking(b["id"])
            assert result["stage"] == "no_worker_available"
            assert any(n["delivered_at"] and n.get("message") for n in result["notifications"])
            assert any(e["reason"] == "assignment_not_accepted" for e in result["escalations"])
            assert not (await store.worker("worker-a"))["reservations"]
            count = len(result["escalations"])
            await process_due(service, now + timedelta(hours=2))
            assert len((await store.booking(b["id"]))["escalations"]) == count
            return result

    result = asyncio.run(sweep())
    notice = next(n for n in result["notifications"] if n["delivered_at"])
    response = post(
        c,
        h["citizen-a"],
        f"/requests/{b['id']}/notifications/{notice['id']}/acknowledge",
        {"revision": result["revision"] + 1},
    )
    assert response.status_code == 200, response.text
