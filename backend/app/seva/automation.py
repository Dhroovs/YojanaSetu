from datetime import timedelta
from types import SimpleNamespace

from fastapi import HTTPException

from app.agents.case_agents import FollowUpAgent
from app.cases.models import Actor, CaseNotice, Event, Preferences, UserRole, now_utc
from app.cases.service import fingerprint
from app.seva.models import TERMINAL, VisitStage

MESSAGES = {
    "en": "Your SevaSetu assistance request has an update. Open the request for details.",
    "hi": "आपके सेवासेतु सहायता अनुरोध में अपडेट है। विवरण के लिए अनुरोध खोलें।",
    "te": "మీ సేవాసేతు సహాయ అభ్యర్థనకు నవీకరణ ఉంది. వివరాల కోసం అభ్యర్థనను తెరవండి.",
}


async def sync_case(service, booking):
    if not booking.get("case_sync_pending") or not booking["case_id"]:
        return
    key = fingerprint(["seva-completed", booking["id"]])
    event = Event(
        actor_id="system:seva",
        action="doorstep_completion_reviewed",
        note=f"SevaSetu visit {booking['id']} completed internal human review.",
    )
    await service.store.db.assistance_cases.update_one(
        {
            "id": booking["case_id"],
            "owner_id": booking["owner_id"],
            "retention_purging": {"$ne": True},
            "operations.key": {"$ne": key},
            "$expr": {"$lt": [{"$size": "$activity"}, 1500]},
        },
        {
            "$push": {
                "activity": event.model_dump(mode="python"),
                "notices": CaseNotice(
                    event_id=event.id, action=event.action, due_at=now_utc()
                ).model_dump(mode="python"),
                "operations": {"key": key, "action": "seva_completion", "fingerprint": key},
            },
            "$inc": {"revision": 1},
            "$set": {"updated_at": now_utc(), "next_automation_at": now_utc()},
        },
    )
    recorded = await service.store.db.assistance_cases.find_one(
        {"id": booking["case_id"], "owner_id": booking["owner_id"], "operations.key": key},
        {"id": 1},
    )
    if recorded:
        booking["case_sync_pending"] = False


async def process_due(service, now=None, limit=100):
    now = now or now_utc()
    actor = Actor(id="system:seva", username="automation", role=UserRole.admin)
    rows = (
        await service.store.bookings.find({"next_automation_at": {"$lte": now}}, {"_id": 0})
        .sort("next_automation_at", 1)
        .limit(limit)
        .to_list(limit)
    )
    processed = 0
    for booking in rows:
        revision = booking["revision"]
        release = False
        if booking["worker_id"] and booking["stage"] not in {
            s.value for s in TERMINAL | {VisitStage.completed, VisitStage.followup}
        }:
            worker = await service.store.worker(booking["worker_id"])
            if not service.verified(worker, now):
                service.escalate(booking, "worker_verification_expired_or_suspended")
        if booking["appointment"] and booking["stage"] in {
            VisitStage.scheduled,
            VisitStage.en_route,
        }:
            if booking["appointment"]["end"] + timedelta(hours=1) < now:
                booking["stage"] = VisitStage.no_show.value
                booking["missed_count"] = booking.get("missed_count", 0) + 1
                service.escalate(
                    booking, "repeated_no_show" if booking["missed_count"] >= 2 else "missed_visit"
                )
                service.notify(booking, "missed_visit")
                service.audit(booking, actor, "appointment_missed")
                release = True
        elif (
            booking["stage"] == VisitStage.assigned
            and booking["updated_at"] + timedelta(hours=24) < now
        ):
            booking["stage"] = VisitStage.unavailable.value
            service.escalate(booking, "assignment_not_accepted")
            release = True
        for notice in booking["notifications"]:
            if notice.get("delivered_at") or notice.get("cancelled_at") or notice["due_at"] > now:
                continue
            if notice["kind"] == "appointment_reminder" and booking["stage"] not in {
                VisitStage.scheduled,
                VisitStage.en_route,
                VisitStage.in_progress,
            }:
                notice["cancelled_at"] = now
                continue
            prefs = Preferences.model_validate(booking["preferences"])
            last = booking.get("last_notification_at")
            allowed = FollowUpAgent().next_allowed(
                SimpleNamespace(
                    preferences=prefs, reminders=[SimpleNamespace(created_at=last)] if last else []
                ),
                now,
                service.settings.seva_notification_interval_hours,
            )
            if not prefs.in_app:
                notice["due_at"] = now + timedelta(days=1)
            elif allowed > now:
                notice["due_at"] = allowed
            else:
                notice.update(
                    delivered_at=now, message=MESSAGES.get(notice["language"], MESSAGES["en"])
                )
                booking["last_notification_at"] = now
        if booking["case_sync_pending"]:
            await sync_case(service, booking)
        if (
            booking["stage"] in {s.value for s in TERMINAL}
            and booking["updated_at"] + timedelta(days=service.settings.seva_retention_days) < now
        ):
            booking["location"] = {
                "district": "Removed",
                "mandal": "Removed",
                "village": "Removed",
                "address": "Removed under retention policy",
            }
            booking["description"] = "Removed under retention policy"
            if booking.get("outcome"):
                booking["outcome"]["note"] = "Removed under retention policy"
                booking["outcome"]["documents_assisted"] = []
                booking["outcome"]["task_checklist"] = []
                booking["outcome"].pop("review_note", None)
            if booking.get("feedback"):
                booking["feedback"]["note"] = "Removed under retention policy"
            for event in booking["audit"]:
                event["note"] = "Removed under retention policy"
            for escalation in booking["escalations"]:
                escalation.pop("resolution_note", None)
        pending = [
            n["due_at"]
            for n in booking["notifications"]
            if not n.get("delivered_at") and not n.get("cancelled_at")
        ]
        booking["next_automation_at"] = min([now + timedelta(hours=1), *pending])
        booking["revision"] = revision + 1
        try:
            await service.store.save(booking, revision)
            if release:
                await service.store.release(booking["worker_id"], booking["id"])
            processed += 1
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
    # Reconcile conservative reservations left by interrupted, known-cancelled operations.
    for worker in (
        await service.store.workers.find({"reservations.0": {"$exists": True}}, {"_id": 0})
        .limit(limit)
        .to_list(limit)
    ):
        for reservation in worker["reservations"]:
            booking = await service.store.booking(reservation["booking_id"])
            expected = reservation.get("expected_booking_revision")
            invalid = (
                not booking
                or expected is not None
                and booking["revision"] > expected
                and (
                    booking["worker_id"] != worker["id"]
                    or booking["stage"]
                    in {
                        s.value
                        for s in TERMINAL
                        | {
                            VisitStage.completed,
                            VisitStage.followup,
                            VisitStage.no_show,
                            VisitStage.unavailable,
                        }
                    }
                )
            )
            if invalid:
                await service.store.release(worker["id"], reservation["booking_id"])
    return processed
