from copy import deepcopy
from datetime import timedelta

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.cases.models import UserRole, new_id, now_utc
from app.cases.service import fingerprint, operation_key
from app.seva.models import TERMINAL, VisitStage, fresh_booking


def reviewer(actor):
    if actor.role not in {UserRole.admin, UserRole.coordinator}:
        raise HTTPException(403, "Coordinator access is required.")


class SevaService:
    def __init__(self, store, cases, auth, settings):
        self.store, self.cases, self.auth, self.settings = store, cases, auth, settings

    async def authorized(self, booking_id, actor):
        booking = await self.store.booking(booking_id)
        if not booking or not (
            actor.role == UserRole.admin
            or actor.role == UserRole.citizen
            and booking["owner_id"] == actor.id
            or actor.role == UserRole.coordinator
            and booking["coordinator_id"] == actor.id
            or actor.role == UserRole.worker
            and booking["worker_id"] == actor.id
        ):
            raise HTTPException(404, "Doorstep request not found for this account.")
        if actor.role == UserRole.worker:
            worker = await self.store.worker(actor.id)
            if not self.verified(worker, now_utc()):
                raise HTTPException(403, "Worker verification is inactive or expired.")
        return booking

    def view(self, booking, actor):
        result = deepcopy(booking)
        for key in ("_id", "creation_key", "creation_fingerprint", "operations"):
            result.pop(key, None)
        if actor.role == UserRole.worker and not booking["assignment_accepted"]:
            result["location"] = {
                "district": booking["location"]["district"],
                "mandal": booking["location"]["mandal"],
                "village": booking["location"]["village"],
                "address": "Available after assignment acceptance",
            }
        return result

    def audit(self, booking, actor, action, note=""):
        if len(booking["audit"]) >= 1000:
            raise HTTPException(409, "Audit capacity reached; contact the administrator.")
        booking["audit"].append(
            {
                "id": new_id(),
                "actor_id": actor.id,
                "role": actor.role,
                "action": action,
                "note": note,
                "at": now_utc(),
            }
        )

    def notify(self, booking, kind, due=None):
        key = f"{kind}:{booking['revision']}"
        if not any(n["key"] == key for n in booking["notifications"]):
            booking["notifications"].append(
                {
                    "id": new_id(),
                    "key": key,
                    "kind": kind,
                    "due_at": due or now_utc(),
                    "delivered_at": None,
                    "acknowledged_by": [],
                    "language": booking["language"],
                }
            )
        booking["next_automation_at"] = min(booking["next_automation_at"], due or now_utc())

    def escalate(self, booking, reason):
        if not any(e["reason"] == reason and e["status"] == "open" for e in booking["escalations"]):
            booking["escalations"].append(
                {
                    "id": new_id(),
                    "reason": reason,
                    "status": "open",
                    "severity": "high"
                    if reason in {"disputed_completion", "repeated_no_show"}
                    else "normal",
                    "coordinator_id": booking["coordinator_id"],
                    "created_at": now_utc(),
                }
            )
            self.notify(booking, "escalation")

    async def create(self, body, actor, key):
        if actor.role != UserRole.citizen:
            raise HTTPException(403, "Citizens create requests owned by their own account.")
        if body.preferred_window.start <= now_utc():
            raise HTTPException(422, "Choose a future service window.")
        if body.case_id:
            await self.cases.authorized(body.case_id, actor)
        if body.scheme_id and not await self.store.db.schemes.find_one({"id": body.scheme_id}):
            raise HTTPException(404, "Scheme not found.")
        hashed = operation_key(key)
        booking = fresh_booking(body, actor.id, hashed, fingerprint(body.model_dump(mode="json")))
        self.audit(booking, actor, "requested")
        self.notify(booking, "request_received")
        try:
            await self.store.bookings.insert_one(deepcopy(booking))
        except DuplicateKeyError:
            booking = await self.store.bookings.find_one(
                {"owner_id": actor.id, "creation_key": hashed}, {"_id": 0}
            )
            if booking["creation_fingerprint"] != fingerprint(body.model_dump(mode="json")):
                raise HTTPException(409, "Idempotency key reused for a different request.")
        return self.view(booking, actor)

    async def mutate(self, booking_id, actor, body, key, action, change, *, claim=False):
        booking = (
            await self.store.booking(booking_id)
            if claim
            else await self.authorized(booking_id, actor)
        )
        if not booking:
            raise HTTPException(404, "Doorstep request not found.")
        if claim:
            reviewer(actor)
            if actor.role != UserRole.admin and booking["coordinator_id"] not in {None, actor.id}:
                raise HTTPException(404, "Doorstep request not available for claim.")
        hashed, digest = (
            operation_key(key),
            fingerprint(body.model_dump(mode="json", exclude={"revision"})),
        )
        existing = next((o for o in booking["operations"] if o["key"] == hashed), None)
        if existing:
            if existing["action"] != action or existing["fingerprint"] != digest:
                raise HTTPException(409, "Idempotency key was used for another action.")
            return booking
        if booking["revision"] != body.revision:
            raise HTTPException(409, "Request changed. Refresh before retrying.")
        await change(booking)
        self.audit(booking, actor, action, body.note)
        booking["revision"] += 1
        booking["updated_at"] = now_utc()
        booking["operations"].append({"key": hashed, "fingerprint": digest, "action": action})
        await self.store.save(booking, body.revision)
        return booking

    def verified(self, worker, until):
        return bool(
            worker
            and worker.get("active")
            and worker.get("verification_status")
            in {"verified_internally", "authorization_confirmed"}
            and worker.get("verification_expires_at")
            and worker["verification_expires_at"] > until
        )

    async def worker_profile(self, worker_id, body, actor):
        if not (
            actor.role == UserRole.admin
            or actor.id == worker_id
            and actor.role in {UserRole.worker, UserRole.coordinator}
        ):
            raise HTTPException(403, "Only the worker or administrator may submit a profile.")
        account = await self.auth.user_by_id(worker_id)
        if (
            not account
            or not account.get("active")
            or account["role"] not in {"worker", "coordinator"}
        ):
            raise HTTPException(422, "Choose a provisioned active worker/coordinator account.")
        if body.organization_id and not await self.store.db.seva_organizations.find_one(
            {"id": body.organization_id, "active": True}
        ):
            raise HTTPException(422, "Organization is unknown or inactive.")
        if await self.store.worker(worker_id):
            raise HTTPException(
                409,
                "Profile already exists. Material profile changes require administrator review.",
            )
        record = {
            **body.model_dump(mode="python"),
            "id": worker_id,
            "revision": 0,
            "active": True,
            "verification_status": "pending_verification",
            "verification_expires_at": None,
            "availability": [],
            "reservations": [],
            "verification_history": [],
            "account_role": account["role"],
        }
        await self.store.workers.insert_one(deepcopy(record))
        return self.worker_view(record)

    def worker_view(self, worker):
        result = {k: v for k, v in worker.items() if k not in {"_id", "reservations"}}
        result["current_workload"] = sum(
            r["end"] > now_utc() for r in worker.get("reservations", [])
        )
        result["verification_label"] = (
            "Internal/organization review only; not government certification."
        )
        return result

    async def verify_worker(self, worker_id, body, actor):
        if actor.role != UserRole.admin:
            raise HTTPException(403, "Only administrators may verify or suspend workers.")
        if not body.confirmed or not body.note:
            raise HTTPException(
                422, "Explicit verification confirmation and review note are required."
            )
        if body.status in {"verified_internally", "authorization_confirmed"}:
            if (
                not body.expires_at
                or body.expires_at.tzinfo is None
                or body.expires_at <= now_utc()
            ):
                raise HTTPException(422, "Verification needs a future timezone-aware expiry.")
            if body.status == "authorization_confirmed" and not (
                body.evidence_url or ""
            ).startswith("https://"):
                raise HTTPException(
                    422, "Record the reviewed organization authorization evidence URL."
                )
        result = await self.store.workers.update_one(
            {"id": worker_id, "revision": body.revision},
            {
                "$set": {
                    "verification_status": body.status,
                    "verification_expires_at": body.expires_at,
                    "active": body.status != "suspended",
                },
                "$inc": {"revision": 1},
                "$push": {
                    "verification_history": {
                        "actor_id": actor.id,
                        "at": now_utc(),
                        "status": body.status,
                        "note": body.note,
                        "evidence_url": body.evidence_url,
                    }
                },
            },
        )
        if not result.matched_count:
            raise HTTPException(409, "Worker changed or was not found.")
        return self.worker_view(await self.store.worker(worker_id))

    async def availability(self, worker_id, body, actor):
        if actor.id != worker_id and actor.role != UserRole.admin:
            raise HTTPException(403, "Only the worker or administrator may change availability.")
        worker = await self.store.worker(worker_id)
        if not worker:
            raise HTTPException(404, "Worker profile not found.")
        for r in worker["reservations"]:
            if r["end"] > now_utc() and not any(
                s.start <= r["start"] and s.end >= r["end"] for s in body.slots
            ):
                raise HTTPException(
                    409, "Availability cannot remove a reserved appointment window."
                )
        result = await self.store.workers.update_one(
            {"id": worker_id, "revision": body.revision},
            {
                "$set": {"availability": [s.model_dump(mode="python") for s in body.slots]},
                "$inc": {"revision": 1},
            },
        )
        if not result.matched_count:
            raise HTTPException(409, "Calendar changed. Refresh availability.")
        return self.worker_view(await self.store.worker(worker_id))

    async def candidates(self, booking, window):
        if not booking["share_with_assigned_worker"]:
            return []
        workers = await self.store.workers.find(
            {"active": True, "account_role": "worker"}, {"_id": 0}
        ).to_list(500)
        output = []
        for worker in workers:
            if not self.verified(worker, window.end):
                continue
            account = await self.auth.user_by_id(worker["id"])
            if not account or not account.get("active"):
                continue
            if (
                booking["category"] not in worker["categories"]
                or booking["language"] not in worker["languages"]
            ):
                continue
            if booking["location"]["district"].casefold() not in [
                d.casefold() for d in worker["districts"]
            ]:
                continue
            if worker["areas"] and not any(
                a.casefold()
                in {
                    booking["location"]["mandal"].casefold(),
                    booking["location"]["village"].casefold(),
                }
                for a in worker["areas"]
            ):
                continue
            if not set(booking["accessibility"]).issubset(worker["capabilities"]):
                continue
            if worker["organization_id"] and not await self.store.db.seva_organizations.find_one(
                {"id": worker["organization_id"], "active": True}
            ):
                continue
            if not any(
                s["start"] <= window.start and s["end"] >= window.end
                for s in worker["availability"]
            ):
                continue
            if any(
                r["start"] < window.end and r["end"] > window.start for r in worker["reservations"]
            ):
                continue
            workload = sum(r["end"] > now_utc() for r in worker["reservations"])
            if workload >= worker["capacity"]:
                continue
            output.append(
                {
                    "worker_id": worker["id"],
                    "display_name": worker["display_name"],
                    "workload": workload,
                    "verification": worker["verification_status"],
                    "reasons": [
                        "Verified internally/current authorization",
                        "Service area and category match",
                        "Language and accessibility match",
                        "Declared availability; no conflicting reservation",
                    ],
                    "window": window.model_dump(mode="json"),
                }
            )
        return sorted(output, key=lambda w: (w["workload"], w["worker_id"]))

    async def assign(self, booking_id, actor, body, key):
        reviewer(actor)
        booking = await self.authorized(booking_id, actor)
        receipt = next((o for o in booking["operations"] if o["key"] == operation_key(key)), None)
        if receipt:
            if receipt["action"] != "assignment" or receipt["fingerprint"] != fingerprint(
                body.model_dump(mode="json", exclude={"revision"})
            ):
                raise HTTPException(409, "Idempotency key was used for another action.")
            return self.view(booking, actor)
        if not body.confirmed:
            raise HTTPException(422, "Coordinator must confirm this assignment proposal.")
        if booking["stage"] not in {
            VisitStage.approved,
            VisitStage.unavailable,
            VisitStage.reschedule,
            VisitStage.no_show,
        }:
            raise HTTPException(409, "Request must be approved and unassigned before assignment.")
        if body.window.start <= now_utc():
            raise HTTPException(422, "Choose a future appointment window.")
        if body.worker_id not in {
            c["worker_id"] for c in await self.candidates(booking, body.window)
        }:
            raise HTTPException(
                409, "Worker is not eligible/available. An override cannot bypass eligibility."
            )
        worker = await self.store.worker(body.worker_id)
        await self.store.reserve(worker, booking_id, body.window, now_utc(), body.revision)
        old_worker = booking["worker_id"]

        async def change(current):
            current.update(
                worker_id=body.worker_id,
                appointment=body.window.model_dump(mode="python"),
                assignment_accepted=False,
                stage=VisitStage.assigned.value,
            )
            self.notify(current, "assignment_proposed")

        try:
            result = await self.mutate(booking_id, actor, body, key, "assignment", change)
        except HTTPException:
            await self.store.release(body.worker_id, booking_id)
            raise
        if old_worker and old_worker != body.worker_id:
            await self.store.release(old_worker, booking_id)
        return self.view(result, actor)

    async def action(self, booking_id, actor, body, key):
        action = body.action
        if action in {
            "approve",
            "reject",
            "claim",
            "confirm_completion",
            "no_show",
            "close",
            "resolve_escalation",
        }:
            reviewer(actor)
        released = []

        async def change(b):
            stage = VisitStage(b["stage"])
            is_owner = actor.role == UserRole.citizen and actor.id == b["owner_id"]
            is_worker = actor.role == UserRole.worker and actor.id == b["worker_id"]
            if action == "claim":
                if stage in TERMINAL:
                    raise HTTPException(409, "Closed requests cannot be claimed.")
                if not body.confirmed:
                    raise HTTPException(422, "Confirm taking responsibility for this request.")
                b["coordinator_id"] = actor.id
            elif action == "approve":
                if (
                    stage not in {VisitStage.pending, VisitStage.escalated}
                    or not b["share_with_assigned_worker"]
                ):
                    raise HTTPException(409, "Consent and pending coordinator review are required.")
                b["stage"] = VisitStage.approved.value
            elif action == "reject":
                if stage not in {VisitStage.pending, VisitStage.approved} or not body.note:
                    raise HTTPException(
                        409, "Only pending/approved requests may be rejected with a reason."
                    )
                b["stage"] = VisitStage.rejected.value
            elif action == "cancel":
                if (
                    not (is_owner or actor.role in {UserRole.admin, UserRole.coordinator})
                    or stage in TERMINAL
                ):
                    raise HTTPException(403, "Cancellation is unavailable for this actor/state.")
                if not body.confirmed:
                    raise HTTPException(422, "Confirm cancellation.")
                b["stage"] = VisitStage.cancelled.value
                released.append(b["worker_id"])
                self.notify(b, "cancelled")
            elif action in {"accept", "decline"}:
                if not is_worker or stage != VisitStage.assigned:
                    raise HTTPException(
                        403, "Only the proposed worker may accept/decline this assignment."
                    )
                if action == "decline":
                    released.append(b["worker_id"])
                    b.update(
                        worker_id=None,
                        appointment=None,
                        assignment_accepted=False,
                        stage=VisitStage.unavailable.value,
                    )
                else:
                    worker = await self.store.worker(actor.id)
                    if not self.verified(worker, b["appointment"]["end"]) or not any(
                        r["booking_id"] == booking_id for r in worker["reservations"]
                    ):
                        raise HTTPException(
                            409, "Worker verification/reservation is no longer valid."
                        )
                    b.update(assignment_accepted=True, stage=VisitStage.scheduled.value)
                    self.notify(b, "appointment_confirmed")
                    self.notify(
                        b,
                        "appointment_reminder",
                        max(now_utc(), b["appointment"]["start"] - timedelta(hours=2)),
                    )
            elif action in {"en_route", "check_in"}:
                if not is_worker or stage not in {VisitStage.scheduled, VisitStage.en_route}:
                    raise HTTPException(
                        403, "Only the accepted worker can check in to a scheduled visit."
                    )
                if now_utc() < b["appointment"]["start"] - timedelta(minutes=30) or now_utc() > b[
                    "appointment"
                ]["end"] + timedelta(hours=2):
                    raise HTTPException(
                        409, "Check-in is outside the appointment window. Ask for rescheduling."
                    )
                b["stage"] = (
                    VisitStage.en_route.value
                    if action == "en_route"
                    else VisitStage.in_progress.value
                )
            elif action == "submit_outcome":
                if (
                    not is_worker
                    or stage != VisitStage.in_progress
                    or not body.note
                    or not body.services_performed
                ):
                    raise HTTPException(
                        409,
                        "Accepted worker must check in and record performed services and notes.",
                    )
                b["outcome"] = {
                    "note": body.note,
                    "services_performed": body.services_performed,
                    "documents_assisted": body.documents_assisted,
                    "task_checklist": body.task_checklist,
                    "submitted_by": actor.id,
                    "at": now_utc(),
                    "reviewed_by": None,
                    "reviewed_at": None,
                }
                b["stage"] = VisitStage.completion_review.value
            elif action == "confirm_completion":
                if (
                    stage != VisitStage.completion_review
                    or not b["outcome"]
                    or not body.confirmed
                    or not body.note
                ):
                    raise HTTPException(
                        422, "Coordinator must explicitly review the submitted outcome with a note."
                    )
                b["outcome"].update(
                    reviewed_by=actor.id, reviewed_at=now_utc(), review_note=body.note
                )
                b["stage"] = VisitStage.completed.value
                b["case_sync_pending"] = bool(b["case_id"])
                self.notify(b, "completion_reviewed")
                released.append(b["worker_id"])
            elif action == "citizen_confirm":
                if not is_owner or stage not in {
                    VisitStage.completion_review,
                    VisitStage.completed,
                }:
                    raise HTTPException(403, "Only the owner may confirm a recorded visit outcome.")
                b["citizen_confirmed"] = True
            elif action == "reschedule":
                if (
                    stage in TERMINAL
                    or not (is_owner or actor.role in {UserRole.admin, UserRole.coordinator})
                    or not body.window
                    or body.window.start <= now_utc()
                ):
                    raise HTTPException(
                        409, "Provide a future proposed window on an active authorized request."
                    )
                if not body.confirmed:
                    raise HTTPException(
                        422,
                        "Confirm rescheduling; a new worker acceptance will be required.",
                    )
                released.append(b["worker_id"])
                b.update(
                    preferred_window=body.window.model_dump(mode="python"),
                    worker_id=None,
                    appointment=None,
                    assignment_accepted=False,
                    stage=VisitStage.reschedule.value,
                )
                self.notify(b, "rescheduling_requested")
            elif action == "report_problem":
                if not body.note or stage in {VisitStage.cancelled, VisitStage.rejected}:
                    raise HTTPException(422, "Provide an internal problem description.")
                self.escalate(
                    b,
                    "disputed_completion"
                    if stage in {VisitStage.completed, VisitStage.completion_review}
                    else "citizen_problem",
                )
                b["stage"] = VisitStage.escalated.value
            elif action == "no_show":
                if (
                    stage not in {VisitStage.scheduled, VisitStage.en_route}
                    or now_utc() <= b["appointment"]["end"]
                ):
                    raise HTTPException(
                        409, "Only an overdue, not-started appointment may be marked missed."
                    )
                b["stage"] = VisitStage.no_show.value
                b["missed_count"] = b.get("missed_count", 0) + 1
                released.append(b["worker_id"])
                self.escalate(b, "repeated_no_show" if b["missed_count"] >= 2 else "missed_visit")
                self.notify(b, "missed_visit")
            elif action == "request_followup":
                if (
                    stage != VisitStage.completed
                    or not body.followup_at
                    or body.followup_at.tzinfo is None
                    or body.followup_at <= now_utc()
                ):
                    raise HTTPException(
                        422, "A reviewed completed visit and future follow-up time are required."
                    )
                b["stage"] = VisitStage.followup.value
                b["followup_at"] = body.followup_at
                self.notify(b, "followup_reminder", body.followup_at)
            elif action == "feedback":
                if (
                    not is_owner
                    or stage not in {VisitStage.completed, VisitStage.followup, VisitStage.closed}
                    or body.rating is None
                ):
                    raise HTTPException(403, "Only the owner may rate a reviewed completed visit.")
                b["feedback"] = {"rating": body.rating, "note": body.note, "at": now_utc()}
            elif action == "close":
                if (
                    stage not in {VisitStage.completed, VisitStage.followup}
                    or not body.confirmed
                    or not body.note
                ):
                    raise HTTPException(
                        422, "Only reviewed completed/follow-up visits can be explicitly closed."
                    )
                b["stage"] = VisitStage.closed.value
            elif action == "resolve_escalation":
                if stage != VisitStage.escalated or not body.confirmed or not body.note:
                    raise HTTPException(
                        422, "Confirmed human review with resolution note is required."
                    )
                for e in b["escalations"]:
                    if e["status"] == "open":
                        e.update(
                            status="resolved",
                            resolved_by=actor.id,
                            resolved_at=now_utc(),
                            resolution_note=body.note,
                        )
                b["stage"] = (
                    VisitStage.completion_review.value
                    if b["outcome"]
                    else VisitStage.approved.value
                )

        booking = await self.mutate(
            booking_id, actor, body, key, action, change, claim=action == "claim"
        )
        for worker_id in released:
            await self.store.release(worker_id, booking_id)
        return self.view(booking, actor)
