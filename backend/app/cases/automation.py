from datetime import timedelta

from fastapi import HTTPException

from app.agents.case_agents import DocumentVerifier, EscalationAgent, FollowUpAgent
from app.cases.models import Actor, Reminder, ReviewStatus, Stage, UserRole, now_utc
from app.cases.notifications import InAppDevelopmentNotifications


async def process_due(service, now=None, limit=100):
    now = now or now_utc()
    actor = Actor(id="system:durable-worker", username="automation", role=UserRole.admin)
    count = 0
    for case in await service.store.due_cases(now, limit):
        revision = case.revision
        delivered = []
        for followup in case.followups:
            if followup.status != "scheduled" or followup.due_at > now:
                continue
            if (
                followup.reason == "missing_documents"
                and not DocumentVerifier().analyze(case, now)["missing_item_ids"]
            ):
                followup.status = "cancelled"
                continue
            allowed = FollowUpAgent().next_allowed(
                case, now, service.settings.follow_up_interval_hours
            )
            if not case.preferences.in_app:
                followup.due_at = now + timedelta(days=1)
                continue
            if allowed > now:
                followup.due_at = allowed
                continue
            if len(case.reminders) >= 500:
                followup.due_at = now + timedelta(days=1)
                continue
            if not any(r.follow_up_id == followup.id for r in case.reminders):
                reminder = Reminder(
                    id=followup.id, follow_up_id=followup.id, reason=followup.reason, created_at=now
                )
                case.reminders.append(reminder)
                delivered.append(reminder)
                service.event(case, actor, "reminder_delivered", followup.reason, now)
            followup.status = "delivered"
        for trigger in EscalationAgent(service.settings).analyze(case, now)["triggers"]:
            service.escalate(case, actor, trigger["reason"], trigger["severity"], now)
        if DocumentVerifier().analyze(case, now)["missing_item_ids"] and not any(
            f.reason == "missing_documents" and f.status == "scheduled" for f in case.followups
        ):
            service.schedule(
                case,
                actor,
                "missing_documents",
                now + timedelta(hours=service.settings.follow_up_interval_hours),
            )
        future = [f.due_at for f in case.followups if f.status == "scheduled"]
        case.next_automation_at = min([now + timedelta(hours=1), *future])
        case.updated_at, case.revision = now, revision + 1
        try:
            await service.store.save(case, revision)
            for reminder in delivered:
                InAppDevelopmentNotifications().delivered(case.id, reminder.id)
            count += 1
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            # Another durable worker or user won the CAS. Its reminder list is authoritative.
    return count


async def purge_expired(service, now=None, limit=100):
    now = now or now_utc()
    collection = service.store.collection
    records = (
        await collection.find(
            {
                "$or": [
                    {
                        "documents": {
                            "$elemMatch": {
                                "storage_removed": {"$ne": True},
                                "$or": [
                                    {"expires_at": {"$lte": now}},
                                    {"deleted_at": {"$ne": None}},
                                ],
                            }
                        }
                    },
                    {
                        "stage": "closed",
                        "closed_at": {
                            "$lte": now
                            - timedelta(days=service.settings.closed_case_retention_days)
                        },
                    },
                ]
            },
            {"id": 1},
        )
        .limit(limit)
        .to_list(limit)
    )
    count = 0
    actor = Actor(id="system:retention", username="retention", role=UserRole.admin)
    for record in records:
        case = await service.store.load(record["id"])
        if case is None:
            continue
        revision = case.revision
        closed_due = (
            case.stage == Stage.closed
            and case.closed_at
            and now - case.closed_at >= timedelta(days=service.settings.closed_case_retention_days)
        )
        if closed_due:
            claim = await collection.update_one(
                {"id": case.id, "revision": revision, "stage": "closed"},
                {"$set": {"retention_purging": True}, "$inc": {"revision": 1}},
            )
            if not claim.matched_count:
                continue
            # Purging flag blocks reads/reopening; revision CAS excludes in-flight mutations.
            for doc in case.documents:
                service.storage.delete(doc.storage_key)
            await collection.delete_one({"id": case.id, "retention_purging": True})
            count += 1
            continue
        for doc in case.documents:
            if not doc.storage_removed and (doc.deleted_at or doc.expires_at <= now):
                service.storage.delete(doc.storage_key)
                doc.storage_removed = True
                if not doc.deleted_at:
                    doc.deleted_at, doc.review_status = now, ReviewStatus.missing
                    service.event(case, actor, "document_retention_expired", now=now)
        case.revision += 1
        if (
            case.stage == Stage.ready_for_human_review
            and not DocumentVerifier().analyze(case, now)["ready_for_human_review"]
        ):
            service.stage(case, Stage.documents_pending)
        try:
            await service.store.save(case, revision)
        except HTTPException:
            pass  # Deleted content stays inaccessible; next sweep reconciles metadata.
        count += 1
    return count
