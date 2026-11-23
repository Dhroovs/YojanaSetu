import asyncio
import os
from datetime import timedelta
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from test_phase3_mongo import live as live
from test_seva import act, assign, claim_approve, create, post, window, worker

from app.cases.models import now_utc
from app.cases.runtime import PrivateRuntime
from app.seva.automation import MESSAGES, process_due, sync_case
from app.seva.service import SevaService
from app.seva.store import SevaStore

pytestmark = pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")


async def runtime(settings, fn):
    async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
        db = mongo[settings.mongodb_database]
        private = PrivateRuntime(db, settings)
        return await fn(SevaService(SevaStore(db), private.cases, private.auth, settings), db)


def test_withdrawal_revokes_assignment_and_worker_access(live):
    c, h, settings = live
    slot = window()
    worker(c, h, slot)
    b = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    b = assign(c, h["coord-a"], b, slot).json()
    b = act(c, h["worker-a"], b, "accept").json()
    prefs = {
        "revision": b["revision"],
        "confirmed": True,
        "language": "te",
        "share_with_assigned_worker": False,
        "preferences": {"in_app": False, "quiet_start": 21, "quiet_end": 8},
    }
    assert post(c, h["citizen-b"], f"/requests/{b['id']}/preferences", prefs).status_code == 404
    response = post(c, h["citizen-a"], f"/requests/{b['id']}/preferences", prefs)
    assert response.status_code == 200, response.text
    b = response.json()
    assert b["worker_id"] is None and b["stage"] == "pending_coordinator_review"
    assert c.get(f"/api/seva/requests/{b['id']}", headers=h["worker-a"]).status_code == 404

    async def check(service, db):
        assert not (await service.store.worker("worker-a"))["reservations"]

    asyncio.run(runtime(settings, check))


def test_material_profile_change_resets_verification_and_held_visit_blocks_edit(live):
    c, h, _ = live
    slot = window()
    worker(c, h, slot)
    profile = c.get("/api/seva/workers/worker-a", headers=h["worker-a"]).json()
    keys = [
        "display_name",
        "organization_id",
        "kind",
        "categories",
        "languages",
        "districts",
        "areas",
        "capabilities",
        "qualifications",
        "capacity",
    ]
    body = {
        "revision": profile["revision"],
        "profile": {k: profile[k] for k in keys},
        "active": True,
        "confirmed": True,
        "note": "Synthetic training update",
    }
    assert post(c, h["citizen-a"], "/workers/worker-a/profile", body).status_code == 403
    response = post(c, h["worker-a"], "/workers/worker-a/profile", body)
    assert response.status_code == 200, response.text
    assert response.json()["verification_status"] == "pending_verification"
    verified = post(
        c,
        h["admin-a"],
        "/workers/worker-a/verification",
        {
            "revision": response.json()["revision"],
            "confirmed": True,
            "note": "Synthetic re-review",
            "status": "verified_internally",
            "expires_at": (now_utc() + timedelta(days=30)).isoformat(),
        },
    ).json()
    b = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    b = assign(c, h["coord-a"], b, slot).json()
    body["revision"] = verified["revision"] + 1
    assert post(c, h["worker-a"], "/workers/worker-a/profile", body).status_code == 409
    cancelled = act(c, h["citizen-a"], b, "cancel", confirmed=True)
    assert cancelled.status_code == 200
    assert c.get(f"/api/seva/requests/{b['id']}", headers=h["worker-a"]).status_code == 404
    assert c.get("/api/seva/requests?stage=cancelled", headers=h["worker-a"]).status_code == 404


def test_missed_visits_notification_quiet_hours_and_conservative_recovery(live):
    c, h, settings = live
    slot = window()
    worker(c, h, slot)
    b = claim_approve(c, h["coord-a"], create(c, h["citizen-a"], slot))
    b = assign(c, h["coord-a"], b, slot).json()
    b = act(c, h["worker-a"], b, "accept").json()

    async def check(service, db):
        now = (now_utc() + timedelta(days=1)).replace(hour=19, minute=0)  # 00:30 India time.
        notices = (await service.store.booking(b["id"]))["notifications"]
        for notice in notices:
            notice.update(language="te", due_at=now - timedelta(seconds=1))
        await db.seva_requests.update_one(
            {"id": b["id"]},
            {
                "$set": {
                    "appointment.start": now - timedelta(hours=3),
                    "appointment.end": now - timedelta(hours=2),
                    "next_automation_at": now - timedelta(seconds=1),
                    "language": "te",
                    "notifications": notices,
                }
            },
        )
        await process_due(service, now)
        missed = await service.store.booking(b["id"])
        assert missed["stage"] == "no_show" and missed["missed_count"] == 1
        assert not any(n["delivered_at"] for n in missed["notifications"])
        assert not (await service.store.worker("worker-a"))["reservations"]
        await process_due(service, now + timedelta(hours=10))
        missed = await service.store.booking(b["id"])
        assert missed["missed_count"] == 1
        assert any(n.get("message") == MESSAGES["te"] for n in missed["notifications"])
        # A reservation held before the booking CAS may still commit: keep it.
        await db.seva_workers.update_one(
            {"id": "worker-a"},
            {
                "$push": {
                    "reservations": {
                        "booking_id": b["id"],
                        "start": now,
                        "end": now + timedelta(hours=1),
                        "expected_booking_revision": missed["revision"],
                    }
                }
            },
        )
        await process_due(service, now + timedelta(hours=10))
        assert (await service.store.worker("worker-a"))["reservations"]
        await db.seva_requests.update_one({"id": b["id"]}, {"$inc": {"revision": 1}})
        await process_due(service, now + timedelta(hours=10))
        assert not (await service.store.worker("worker-a"))["reservations"]

    asyncio.run(runtime(settings, check))


def test_case_outbox_is_idempotent_and_retention_redacts_free_text(live):
    c, h, settings = live
    case = c.post(
        "/api/cases",
        headers={**h["citizen-a"], "Idempotency-Key": str(uuid4())},
        json={"scheme_id": "test-source-scheme", "assistance_type": "Synthetic assistance"},
    ).json()
    b = create(c, h["citizen-a"])

    async def check(service, db):
        booking = await service.store.booking(b["id"])
        booking.update(case_id=case["id"], case_sync_pending=True)
        await sync_case(service, booking)
        booking["case_sync_pending"] = True  # Retry after a crash before booking acknowledgement.
        await sync_case(service, booking)
        record = await db.assistance_cases.find_one({"id": case["id"]})
        assert (
            len([e for e in record["activity"] if e["action"] == "doorstep_completion_reviewed"])
            == 1
        )
        now = now_utc()
        await db.seva_requests.update_one(
            {"id": b["id"]},
            {
                "$set": {
                    "stage": "closed",
                    "updated_at": now - timedelta(days=181),
                    "next_automation_at": now,
                    "outcome": {
                        "note": "private",
                        "documents_assisted": ["private"],
                        "task_checklist": ["private"],
                        "review_note": "private",
                    },
                    "escalations": [
                        {"reason": "problem", "status": "resolved", "resolution_note": "private"}
                    ],
                }
            },
        )
        await process_due(service, now)
        result = await service.store.booking(b["id"])
        assert result["location"]["address"] == "Removed under retention policy"
        assert "private" not in str(result["outcome"])
        assert "resolution_note" not in result["escalations"][0]

    asyncio.run(runtime(settings, check))


def test_rescheduling_does_not_bypass_initial_coordinator_review(live):
    c, h, _ = live
    slot = window()
    worker(c, h, slot)
    b = create(c, h["citizen-a"], slot)
    b = act(c, h["citizen-a"], b, "reschedule", confirmed=True, window=slot).json()
    b = act(c, h["coord-a"], b, "claim", confirmed=True).json()
    assert assign(c, h["coord-a"], b, slot).status_code == 409
    b = act(c, h["coord-a"], b, "approve").json()
    assert assign(c, h["coord-a"], b, slot).status_code == 200


def test_admin_organization_controls_and_durable_admission_limit(live):
    c, h, settings = live
    body = {
        "display_name": "Synthetic NGO",
        "kind": "ngo",
        "verified_internally": True,
        "confirmed": True,
    }
    assert post(c, h["worker-a"], "/organizations", body).status_code == 403
    organization = post(c, h["admin-a"], "/organizations", body).json()
    result = post(
        c,
        h["admin-a"],
        f"/organizations/{organization['id']}?revision=0",
        {**body, "active": False},
    )
    assert result.status_code == 200, result.text
    assert c.get("/api/seva/organizations", headers=h["worker-a"]).json() == []
    settings.seva_requests_per_minute = 1
    assert c.get("/api/seva/requests", headers=h["citizen-b"]).status_code == 200
    assert c.get("/api/seva/requests", headers=h["citizen-b"]).status_code == 429
