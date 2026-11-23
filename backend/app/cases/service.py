import asyncio
import hashlib
import json
import re
from datetime import timedelta

from fastapi import HTTPException

from app.agents.case_agents import DocumentVerifier
from app.cases.models import (
    STAGE_STATUS,
    TERMINAL,
    AssistanceCase,
    ChecklistItem,
    Document,
    Escalation,
    Event,
    FollowUp,
    ReviewStatus,
    Stage,
    UserRole,
    now_utc,
)
from app.cases.storage import inspect_document


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def operation_key(key):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{16,128}", key):
        raise HTTPException(
            422, "Provide an Idempotency-Key of 16–128 letters, digits, '-' or '_'."
        )
    return hashlib.sha256(key.encode()).hexdigest()


class CaseService:
    def __init__(self, store, auth, storage, settings):
        self.store, self.auth, self.storage, self.settings = store, auth, storage, settings

    async def authorized(self, case_id, actor):
        case = await self.store.load(case_id)
        if (
            case is None
            or case.retention_purging
            or not (
                actor.role == UserRole.admin
                or actor.role == UserRole.citizen
                and case.owner_id == actor.id
                or actor.role == UserRole.coordinator
                and case.coordinator_id == actor.id
                or actor.role == UserRole.worker
                and actor.id in case.worker_ids
            )
        ):
            raise HTTPException(404, "Case not found for this account.")
        return case

    def reviewer(self, actor):
        if actor.role not in {UserRole.coordinator, UserRole.admin}:
            raise HTTPException(403, "An authorized coordinator must perform this action.")

    def event(self, case, actor, action, note="", now=None):
        if len(case.activity) >= 1500:
            raise HTTPException(409, "Case audit capacity reached. Contact the administrator.")
        event = Event(action=action, actor_id=actor.id, note=note, at=now or now_utc())
        case.activity.append(event)
        if action in {
            "case_created",
            "stage_changed",
            "coordinator_assigned",
            "document_received",
            "document_reviewed",
            "document_deleted",
            "followup_scheduled",
            "escalation_created",
            "escalation_acknowledge",
            "escalation_resolve",
            "escalation_reopen",
        }:
            from app.cases.models import CaseNotice

            case.notices.append(CaseNotice(event_id=event.id, action=action, due_at=event.at))
            case.next_automation_at = min(case.next_automation_at, event.at)

    def stage(self, case, value):
        case.stage = value
        case.status = STAGE_STATUS[value]
        if value == Stage.closed:
            case.closed_at = now_utc()
        if value in TERMINAL:
            for followup in case.followups:
                if followup.status == "scheduled":
                    followup.status = "cancelled"

    async def checklist(self, scheme_id):
        scheme = await self.store.database.schemes.find_one({"id": scheme_id}, {"_id": 0})
        if not scheme:
            raise HTTPException(404, "Scheme not found.")
        demo = scheme.get("is_demo", True)
        versions = {}
        labels = []
        label_sources = {}
        verified = False
        if demo:
            labels = scheme.get("documents", [])
        else:
            for source_id in scheme.get("source_references", []):
                source = await self.store.database.ai_sources.find_one(
                    {"source_id": source_id, "verification_status": "verified"}, {"_id": 0}
                )
                if source:
                    versions[source_id] = source["index_version"]
                    if source.get("required_documents") is not None and source.get(
                        "field_evidence", {}
                    ).get("required_documents"):
                        labels.extend(source["required_documents"])
                        for label in source["required_documents"]:
                            label_sources.setdefault(label, []).append(source_id)
                        verified = True
        items = [
            ChecklistItem(
                id=hashlib.sha256(label.encode()).hexdigest()[:20],
                label=label,
                source_ids=label_sources.get(label, []),
                is_demo=demo,
            )
            for label in dict.fromkeys(labels)
        ]
        return items, verified, demo, versions

    async def create(self, body, actor, key):
        if actor.role != UserRole.citizen:
            raise HTTPException(403, "Citizens create their own assistance cases.")
        key = operation_key(key)
        items, verified, demo, versions = await self.checklist(body.scheme_id)
        now = now_utc()
        case = AssistanceCase(
            **body.model_dump(),
            owner_id=actor.id,
            checklist=items,
            checklist_verified=verified,
            is_demo=demo,
            scheme_source_versions=versions,
            creation_key=key,
            creation_fingerprint=fingerprint(body.model_dump()),
            next_automation_at=now + timedelta(hours=1),
            missing_information=[]
            if verified
            else ["Required document checklist needs verified source review."],
        )
        self.stage(case, Stage.documents_pending)
        self.event(
            case,
            actor,
            "case_created",
            "Fictional demo case" if demo else "Assistance case created",
        )
        if items:
            case.followups.append(
                FollowUp(
                    reason="missing_documents",
                    created_by=actor.id,
                    due_at=now + timedelta(hours=self.settings.follow_up_interval_hours),
                )
            )
        return await self.store.create(case)

    async def mutate(self, case_id, actor, revision, key, action, payload, change):
        case = await self.authorized(case_id, actor)
        hashed, digest = operation_key(key), fingerprint(payload)
        existing = next((o for o in case.operations if o["key"] == hashed), None)
        if existing:
            if existing["action"] != action or existing["fingerprint"] != digest:
                raise HTTPException(409, "Idempotency key was reused for a different action.")
            return case
        if case.revision != revision:
            raise HTTPException(409, "Case changed. Refresh before retrying.")
        await change(case)
        case.revision += 1
        case.updated_at = case.last_human_activity_at = now_utc()
        case.operations.append({"key": hashed, "action": action, "fingerprint": digest})
        if len(case.operations) > 1200:
            raise HTTPException(409, "Case operation capacity reached. Contact the administrator.")
        await self.store.save(case, revision)
        return case

    async def transition(self, case_id, actor, body, key):
        self.reviewer(actor)

        async def change(case):
            allowed = {
                Stage.draft: {Stage.documents_pending, Stage.on_hold, Stage.closed},
                Stage.documents_pending: {
                    Stage.ready_for_human_review,
                    Stage.on_hold,
                    Stage.closed,
                },
                Stage.ready_for_human_review: {
                    Stage.assistance_in_progress,
                    Stage.documents_pending,
                    Stage.on_hold,
                    Stage.closed,
                },
                Stage.assistance_in_progress: {
                    Stage.waiting_for_external_update,
                    Stage.completed,
                    Stage.on_hold,
                    Stage.closed,
                },
                Stage.waiting_for_external_update: {
                    Stage.assistance_in_progress,
                    Stage.completed,
                    Stage.on_hold,
                    Stage.closed,
                },
                Stage.on_hold: {
                    Stage.documents_pending,
                    Stage.ready_for_human_review,
                    Stage.assistance_in_progress,
                    Stage.closed,
                },
                Stage.escalated: {Stage.closed},
                Stage.completed: {Stage.assistance_in_progress, Stage.closed},
                Stage.closed: {Stage.documents_pending},
            }
            if body.stage not in allowed[case.stage]:
                raise HTTPException(409, "That assistance stage transition is not permitted.")
            if (body.stage == Stage.closed or case.stage in TERMINAL) and (
                not body.confirmed or not body.note
            ):
                raise HTTPException(422, "Confirm this sensitive action and provide a reason.")
            if body.stage in {
                Stage.ready_for_human_review,
                Stage.assistance_in_progress,
                Stage.completed,
            }:
                if not DocumentVerifier().analyze(case, now_utc())["ready_for_human_review"]:
                    raise HTTPException(
                        409, "Verified checklist and human-accepted documents are required."
                    )
            note = (
                "User/coordinator-reported external update: "
                if body.reported_external_update
                else "Internal assistance update: "
            ) + body.note
            self.stage(case, body.stage)
            if body.stage != Stage.closed:
                case.closed_at = None
            else:
                for referral in case.escalations:
                    if referral.status != "resolved":
                        referral.status = "resolved"
                        referral.resolved_at = referral.updated_at = now_utc()
                        referral.resolution_note = "Internal case closed: " + body.note
            self.event(case, actor, "stage_changed", note)

        return await self.mutate(
            case_id,
            actor,
            body.revision,
            key,
            "stage",
            body.model_dump(exclude={"revision"}),
            change,
        )

    async def assign(self, case_id, actor, body, key):
        self.reviewer(actor)
        case = await self.store.load(case_id)
        if not case:
            raise HTTPException(404, "Case not found.")
        if actor.role == UserRole.coordinator:
            if (
                case.coordinator_id not in {None, actor.id}
                or body.coordinator_id != actor.id
                or (case.coordinator_id is None and body.worker_ids)
                or (case.coordinator_id == actor.id and body.worker_ids != case.worker_ids)
            ):
                raise HTTPException(
                    403, "Coordinators may claim only unassigned cases for themselves."
                )
            # Confirmed self-claim grants access from a staff-only minimal queue.
            permitted_actor = actor.model_copy(update={"role": UserRole.admin})
        else:
            permitted_actor = actor
        if not body.confirmed:
            raise HTTPException(422, "Confirm the coordinator assignment.")
        user = await self.auth.user_by_id(body.coordinator_id)
        if not user or not user.get("active") or user["role"] not in {"coordinator", "admin"}:
            raise HTTPException(422, "Assigned coordinator must be an active coordinator/admin.")
        for worker_id in body.worker_ids:
            worker = await self.auth.user_by_id(worker_id)
            if not worker or not worker.get("active") or worker["role"] != "worker":
                raise HTTPException(422, "Workers must be active provisioned worker accounts.")

        async def change(current):
            current.coordinator_id = body.coordinator_id
            current.worker_ids = list(dict.fromkeys(body.worker_ids))
            for escalation in current.escalations:
                if escalation.status != "resolved":
                    escalation.owner_coordinator_id = body.coordinator_id
            self.event(current, actor, "coordinator_assigned", body.note)

        return await self.mutate(
            case_id,
            permitted_actor,
            body.revision,
            key,
            "assignment",
            body.model_dump(exclude={"revision"}),
            change,
        )

    async def upload(self, case_id, actor, revision, item_id, data, media_type, key):
        case = await self.authorized(case_id, actor)
        if case.stage in TERMINAL:
            raise HTTPException(409, "Reopen the assistance case before uploading.")
        if item_id not in {item.id for item in case.checklist}:
            raise HTTPException(422, "Select an item from this case's source checklist.")
        clean, extension, content_hash, technical, notes = await asyncio.to_thread(
            inspect_document, data, media_type, self.settings
        )
        if any(
            d.item_id == item_id
            and d.content_hash == content_hash
            and not d.deleted_at
            and d.expires_at > now_utc()
            for d in case.documents
        ):
            return case
        if len(case.documents) >= 50:
            raise HTTPException(409, "Document history limit reached. Contact the coordinator.")
        storage_key = await asyncio.to_thread(self.storage.put, clean, extension)

        async def change(current):
            current.documents.append(
                Document(
                    item_id=item_id,
                    storage_key=storage_key,
                    content_hash=content_hash,
                    media_type=media_type,
                    byte_count=len(clean),
                    uploaded_by=actor.id,
                    expires_at=now_utc() + timedelta(days=self.settings.document_retention_days),
                    technical_status=technical,
                    technical_notes=notes,
                )
            )
            if current.stage not in {Stage.escalated, Stage.on_hold}:
                self.stage(current, Stage.documents_pending)
            self.event(current, actor, "document_received")
            self.event(current, actor, "document_technical_check", "Human review remains required.")

        try:
            result = await self.mutate(
                case_id,
                actor,
                revision,
                key,
                "upload",
                {"item_id": item_id, "hash": content_hash, "media_type": media_type},
                change,
            )
            if not any(d.storage_key == storage_key for d in result.documents):
                await asyncio.to_thread(self.storage.delete, storage_key)
            return result
        except Exception:
            await asyncio.to_thread(self.storage.delete, storage_key)
            raise

    async def review(self, case_id, document_id, actor, body, key):
        self.reviewer(actor)

        async def change(case):
            document = next(
                (d for d in case.documents if d.id == document_id and not d.deleted_at), None
            )
            if not document or document.expires_at <= now_utc():
                raise HTTPException(404, "Document not available.")
            if body.status == ReviewStatus.accepted and not case.checklist_verified:
                raise HTTPException(
                    409, "Source checklist is unverified. Confirm official requirements first."
                )
            if not body.note:
                raise HTTPException(422, "Record a review note; this is not legal authentication.")
            document.review_status = ReviewStatus(body.status)
            document.review_note, document.reviewed_by = body.note, actor.id
            document.reviewed_at = now_utc()
            if DocumentVerifier().analyze(case, now_utc())["ready_for_human_review"]:
                for followup in case.followups:
                    if followup.reason == "missing_documents" and followup.status == "scheduled":
                        followup.status = "cancelled"
                if case.stage == Stage.documents_pending:
                    self.stage(case, Stage.ready_for_human_review)
            elif case.stage == Stage.ready_for_human_review:
                self.stage(case, Stage.documents_pending)
            self.event(case, actor, "document_reviewed", body.note)

        return await self.mutate(
            case_id,
            actor,
            body.revision,
            key,
            "document_review",
            {"document_id": document_id, **body.model_dump(exclude={"revision"})},
            change,
        )

    async def delete_document(self, case_id, document_id, actor, body, key, confirmed):
        if actor.role == UserRole.worker:
            raise HTTPException(
                403, "Only the owner or an authorized reviewer may delete documents."
            )
        if not confirmed:
            raise HTTPException(422, "Confirm deletion of the private document.")
        keys = []

        async def change(case):
            document = next((d for d in case.documents if d.id == document_id), None)
            if not document:
                raise HTTPException(404, "Document not found.")
            document.deleted_at, document.review_status = now_utc(), ReviewStatus.missing
            keys.append(document.storage_key)
            if case.stage == Stage.ready_for_human_review:
                self.stage(case, Stage.documents_pending)
            self.event(case, actor, "document_deleted", body.note)

        case = await self.mutate(
            case_id,
            actor,
            body.revision,
            key,
            "document_delete",
            {"document_id": document_id},
            change,
        )
        for storage_key in keys:
            await asyncio.to_thread(self.storage.delete, storage_key)
        return case

    def schedule(self, case, actor, reason, due_at, note=""):
        if any(
            f.reason == reason and f.due_at == due_at and f.status == "scheduled"
            for f in case.followups
        ):
            return
        if len(case.followups) >= 500:
            raise HTTPException(409, "Follow-up history capacity reached.")
        case.followups.append(
            FollowUp(reason=reason, due_at=due_at, created_by=actor.id, note=note)
        )
        case.next_automation_at = min(case.next_automation_at, due_at)
        self.event(case, actor, "followup_scheduled", note)

    async def followup(self, case_id, actor, body, key):
        if body.due_at <= now_utc():
            raise HTTPException(422, "Choose a future follow-up time with timezone.")

        async def change(case):
            if case.stage in TERMINAL:
                raise HTTPException(409, "Assistance case is inactive.")
            self.schedule(case, actor, body.reason, body.due_at, body.note)

        return await self.mutate(
            case_id,
            actor,
            body.revision,
            key,
            "followup_create",
            body.model_dump(exclude={"revision"}),
            change,
        )

    def escalate(self, case, actor, reason, severity="normal", now=None):
        now = now or now_utc()
        previous = next((e for e in reversed(case.escalations) if e.reason == reason), None)
        if previous and previous.status != "resolved":
            return
        if (
            previous
            and previous.resolved_at
            and now - previous.resolved_at < timedelta(hours=self.settings.escalation_reopen_hours)
        ):
            return
        if len(case.escalations) >= 200:
            raise HTTPException(409, "Escalation history capacity reached.")
        case.escalations.append(
            Escalation(
                reason=reason,
                severity=severity,
                owner_coordinator_id=case.coordinator_id,
                created_at=now,
                updated_at=now,
            )
        )
        if case.stage != Stage.escalated:
            case.resume_stage = case.stage
            self.stage(case, Stage.escalated)
        self.event(case, actor, "escalation_created", reason, now)

    async def escalation_action(self, case_id, escalation_id, actor, body, key):
        self.reviewer(actor)

        async def change(case):
            escalation = next((e for e in case.escalations if e.id == escalation_id), None)
            if not escalation:
                raise HTTPException(404, "Escalation not found.")
            if body.action == "acknowledge":
                if escalation.status != "open":
                    raise HTTPException(409, "Only open escalations can be acknowledged.")
                escalation.status, escalation.acknowledged_by = "acknowledged", actor.id
            elif body.action == "resolve":
                if escalation.status == "resolved" or not body.note:
                    raise HTTPException(
                        422, "An unresolved escalation and resolution note are required."
                    )
                escalation.status, escalation.resolution_note = "resolved", body.note
                escalation.resolved_at = now_utc()
                case.missing_information = [
                    i
                    for i in case.missing_information
                    if i not in {"conflicting_information", "coordinator_flag"}
                ]
                if (
                    all(e.status == "resolved" for e in case.escalations)
                    and case.stage == Stage.escalated
                ):
                    self.stage(case, case.resume_stage or Stage.documents_pending)
            else:
                if escalation.status != "resolved" or case.stage == Stage.closed or not body.note:
                    raise HTTPException(
                        409, "Reopen a resolved referral on an active case with a reason."
                    )
                escalation.status, escalation.reopened_count = "open", escalation.reopened_count + 1
                escalation.resolved_at = None
                if case.stage != Stage.escalated:
                    case.resume_stage = case.stage
                    self.stage(case, Stage.escalated)
            escalation.updated_at = now_utc()
            escalation.owner_coordinator_id = case.coordinator_id
            self.event(case, actor, "escalation_" + body.action, body.note)

        return await self.mutate(
            case_id,
            actor,
            body.revision,
            key,
            "escalation_action",
            {"escalation_id": escalation_id, **body.model_dump(exclude={"revision"})},
            change,
        )
