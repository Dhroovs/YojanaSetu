import asyncio
import hashlib
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.agents.case_agents import DocumentVerifier
from app.auth import current_actor, private_runtime
from app.cases.models import (
    Assignment,
    AssistanceCase,
    AssistanceRequest,
    Change,
    DocumentReview,
    EscalationChange,
    FollowUpCreate,
    Preferences,
    ReviewStatus,
    Stage,
    StageChange,
    UserRole,
    now_utc,
)


def make_case_router():
    router = APIRouter(prefix="/api", tags=["Private assistance"])

    @router.get("/cases")
    async def cases(
        request: Request,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=50),
        stage: Stage | None = None,
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.store.page(actor, page, limit, stage=stage)

    @router.get("/coordinator/queue")
    async def queue(
        request: Request,
        kind: Literal["cases", "reviews", "followups", "escalations", "unassigned"] = "cases",
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=50),
        actor=Depends(current_actor),
    ):
        if actor.role not in {UserRole.worker, UserRole.coordinator, UserRole.admin}:
            raise HTTPException(403, "Staff access is required.")
        runtime = await private_runtime(request)
        if kind == "unassigned":
            runtime.cases.reviewer(actor)
            return await runtime.store.unassigned(page, limit)
        return await runtime.store.page(actor, page, limit, kind)

    @router.get("/coordinator/staff")
    async def staff(request: Request, actor=Depends(current_actor)):
        runtime = await private_runtime(request)
        runtime.cases.reviewer(actor)
        return await runtime.auth.staff()

    @router.get("/cases/{case_id}/checklist")
    async def checklist(case_id: str, request: Request, actor=Depends(current_actor)):
        runtime = await private_runtime(request)
        case = await runtime.cases.authorized(case_id, actor)
        return DocumentVerifier().analyze(case, now_utc())

    @router.get("/cases/{case_id}/activity")
    async def activity(
        case_id: str,
        request: Request,
        page: int = Query(1, ge=1),
        limit: int = Query(30, ge=1, le=100),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        case = await runtime.cases.authorized(case_id, actor)
        return {
            "items": list(reversed(case.activity))[(page - 1) * limit : page * limit],
            "total": len(case.activity),
            "page": page,
            "limit": limit,
        }

    @router.post("/cases/{case_id}/stage", response_model=AssistanceCase)
    async def stage(
        case_id: str,
        request: Request,
        body: StageChange,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.cases.transition(case_id, actor, body, idempotency_key)

    @router.post("/cases/{case_id}/assignment", response_model=AssistanceCase)
    async def assignment(
        case_id: str,
        request: Request,
        body: Assignment,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.cases.assign(case_id, actor, body, idempotency_key)

    @router.post("/cases/{case_id}/documents", response_model=AssistanceCase)
    async def upload(
        case_id: str,
        request: Request,
        item_id: str = Query(max_length=40),
        revision: int = Query(ge=0),
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        await runtime.cases.authorized(case_id, actor)  # Authenticate before reading any bytes.
        maximum = request.app.state.settings.document_max_bytes
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > maximum:
                raise HTTPException(413, "Document exceeds configured size limit.")
        return await runtime.cases.upload(
            case_id,
            actor,
            revision,
            item_id,
            bytes(data),
            request.headers.get("content-type", "").split(";")[0].lower(),
            idempotency_key,
        )

    @router.get("/cases/{case_id}/documents/{document_id}/content")
    async def content(
        case_id: str, document_id: str, request: Request, actor=Depends(current_actor)
    ):
        runtime = await private_runtime(request)
        case = await runtime.cases.authorized(case_id, actor)
        doc = next((d for d in case.documents if d.id == document_id and not d.deleted_at), None)
        if not doc or doc.expires_at <= now_utc():
            raise HTTPException(410, "Document is unavailable or its retention period expired.")
        path = runtime.storage.path(doc.storage_key)
        if not path.is_file():
            raise HTTPException(410, "Document is no longer stored.")
        return FileResponse(
            path,
            media_type=doc.media_type,
            filename=f"assistance-document-{doc.id}{path.suffix}",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store",
                "Content-Security-Policy": "sandbox",
            },
        )

    @router.post("/cases/{case_id}/documents/{document_id}/review", response_model=AssistanceCase)
    async def review(
        case_id: str,
        document_id: str,
        request: Request,
        body: DocumentReview,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.cases.review(case_id, document_id, actor, body, idempotency_key)

    @router.post("/cases/{case_id}/documents/{document_id}/delete", response_model=AssistanceCase)
    async def delete_document(
        case_id: str,
        document_id: str,
        request: Request,
        body: Change,
        confirmed: bool = Query(False),
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.cases.delete_document(
            case_id, document_id, actor, body, idempotency_key, confirmed
        )

    @router.post("/cases/{case_id}/followups", response_model=AssistanceCase)
    async def followup(
        case_id: str,
        request: Request,
        body: FollowUpCreate,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.cases.followup(case_id, actor, body, idempotency_key)

    @router.post(
        "/cases/{case_id}/reminders/{reminder_id}/acknowledge", response_model=AssistanceCase
    )
    async def acknowledge(
        case_id: str,
        reminder_id: str,
        request: Request,
        body: Change,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)

        async def change(case):
            reminder = next((r for r in case.reminders if r.id == reminder_id), None)
            if not reminder:
                raise HTTPException(404, "Reminder not found.")
            if actor.id not in reminder.acknowledged_by:
                reminder.acknowledged_by.append(actor.id)
                runtime.cases.event(case, actor, "reminder_acknowledged")

        return await runtime.cases.mutate(
            case_id,
            actor,
            body.revision,
            idempotency_key,
            "acknowledge",
            {"reminder_id": reminder_id},
            change,
        )

    @router.post("/cases/{case_id}/notices/{notice_id}/acknowledge", response_model=AssistanceCase)
    async def acknowledge_notice(
        case_id: str,
        notice_id: str,
        body: Change,
        request: Request,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)

        async def change(case):
            notice = next((n for n in case.notices if n.id == notice_id and n.delivered_at), None)
            if not notice:
                raise HTTPException(404, "Delivered notice not found.")
            if actor.id not in notice.acknowledged_by:
                notice.acknowledged_by.append(actor.id)
                runtime.cases.event(case, actor, "notice_acknowledged")

        return await runtime.cases.mutate(
            case_id,
            actor,
            body.revision,
            idempotency_key,
            "notice_acknowledge",
            {"notice_id": notice_id},
            change,
        )

    @router.post("/cases/{case_id}/preferences", response_model=AssistanceCase)
    async def preferences(
        case_id: str,
        request: Request,
        body: Preferences,
        revision: int = Query(ge=0),
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)

        async def change(case):
            if actor.role == UserRole.worker:
                raise HTTPException(
                    403, "Only the citizen or reviewer may change notification preferences."
                )
            case.preferences = body
            runtime.cases.event(case, actor, "notification_preferences_updated")

        return await runtime.cases.mutate(
            case_id, actor, revision, idempotency_key, "preferences", body.model_dump(), change
        )

    @router.post("/cases/{case_id}/escalations/{escalation_id}", response_model=AssistanceCase)
    async def escalation(
        case_id: str,
        escalation_id: str,
        request: Request,
        body: EscalationChange,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        return await runtime.cases.escalation_action(
            case_id, escalation_id, actor, body, idempotency_key
        )

    @router.post("/cases/{case_id}/flags", response_model=AssistanceCase)
    async def flag(
        case_id: str,
        request: Request,
        body: Change,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        runtime.cases.reviewer(actor)

        async def change(case):
            if "coordinator_flag" not in case.missing_information:
                case.missing_information.append("coordinator_flag")
            runtime.cases.escalate(case, actor, "conflicting_information", "high")
            runtime.cases.event(case, actor, "coordinator_flag", body.note)

        return await runtime.cases.mutate(
            case_id,
            actor,
            body.revision,
            idempotency_key,
            "flag",
            body.model_dump(exclude={"revision"}),
            change,
        )

    @router.post("/cases/{case_id}/checklist/refresh", response_model=AssistanceCase)
    async def refresh(
        case_id: str,
        request: Request,
        body: Change,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        runtime = await private_runtime(request)
        runtime.cases.reviewer(actor)

        async def change(case):
            items, verified, demo, versions = await runtime.cases.checklist(case.scheme_id)
            if versions != case.scheme_source_versions:
                for doc in case.documents:
                    if not doc.deleted_at:
                        doc.review_status = ReviewStatus.human
                        doc.review_note = (
                            "Source checklist changed; human review is required again."
                        )
            case.checklist, case.checklist_verified, case.is_demo = items, verified, demo
            case.scheme_source_versions = versions
            case.missing_information = (
                [] if verified else ["Required document checklist needs verified source review."]
            )
            if case.stage not in {Stage.escalated, Stage.on_hold, Stage.closed, Stage.completed}:
                runtime.cases.stage(case, Stage.documents_pending)
            runtime.cases.event(case, actor, "source_checklist_refreshed", body.note)

        return await runtime.cases.mutate(
            case_id, actor, body.revision, idempotency_key, "refresh_checklist", {}, change
        )

    @router.post("/cases/{case_id}/assist")
    async def assist(
        case_id: str,
        request: Request,
        body: AssistanceRequest,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        from app.agents.case_orchestrator import CaseOrchestrator
        from app.ai.runtime import matcher_service
        from app.seva.runtime import seva_service

        runtime = await private_runtime(request)
        async with asyncio.timeout(request.app.state.settings.ai_timeout_seconds):
            return await CaseOrchestrator(
                runtime.cases,
                lambda: matcher_service(request),
                hashlib.sha256(request.headers["authorization"].encode()).hexdigest(),
                lambda: seva_service(request),
            ).run(case_id, actor, body, idempotency_key)

    return router
