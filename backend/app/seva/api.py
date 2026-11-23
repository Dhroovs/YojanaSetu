from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.auth import current_actor
from app.cases.models import Change, UserRole, new_id, now_utc
from app.seva.models import (
    Assignment,
    Availability,
    BookingAction,
    BookingInput,
    OrganizationInput,
    WorkerInput,
    WorkerVerification,
)
from app.seva.runtime import seva_service
from app.seva.service import reviewer


def make_router():
    router = APIRouter(prefix="/api/seva", tags=["SevaSetu"])

    @router.post("/requests", status_code=201)
    async def create(
        body: BookingInput,
        request: Request,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        return await (await seva_service(request)).create(body, actor, idempotency_key)

    @router.get("/requests")
    async def requests(
        request: Request,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=50),
        stage: str | None = None,
        unassigned: bool = False,
        actor=Depends(current_actor),
    ):
        service = await seva_service(request)
        if unassigned:
            reviewer(actor)
            query = {"coordinator_id": None}
        elif actor.role == UserRole.admin:
            query = {}
        elif actor.role == UserRole.citizen:
            query = {"owner_id": actor.id}
        elif actor.role == UserRole.worker:
            query = {"worker_id": actor.id}
            if not service.verified(await service.store.worker(actor.id), now_utc()):
                raise HTTPException(403, "Current worker verification is required.")
        else:
            query = {"coordinator_id": actor.id}
        if stage:
            query["stage"] = stage
        projection = (
            {"_id": 0, "id": 1, "category": 1, "stage": 1, "revision": 1, "created_at": 1}
            if unassigned
            else {"_id": 0}
        )
        collection = service.store.bookings
        rows = (
            await collection.find(query, projection)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(limit)
        )
        return {
            "items": rows if unassigned else [service.view(r, actor) for r in rows],
            "total": await collection.count_documents(query),
            "page": page,
            "limit": limit,
        }

    @router.get("/requests/{booking_id}")
    async def detail(booking_id: str, request: Request, actor=Depends(current_actor)):
        service = await seva_service(request)
        return service.view(await service.authorized(booking_id, actor), actor)

    @router.post("/requests/{booking_id}/actions")
    async def action(
        booking_id: str,
        body: BookingAction,
        request: Request,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        return await (await seva_service(request)).action(booking_id, actor, body, idempotency_key)

    @router.post("/requests/{booking_id}/assignment")
    async def assign(
        booking_id: str,
        body: Assignment,
        request: Request,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        return await (await seva_service(request)).assign(booking_id, actor, body, idempotency_key)

    @router.post("/requests/{booking_id}/agent")
    async def agent(
        booking_id: str,
        request: Request,
        assignment: Assignment | None = None,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        from app.agents.doorstep_coordinator import DoorstepCoordinator

        return await DoorstepCoordinator(await seva_service(request)).run(
            booking_id, actor, assignment, idempotency_key
        )

    @router.post("/workers/{worker_id}", status_code=201)
    async def profile(
        worker_id: str, body: WorkerInput, request: Request, actor=Depends(current_actor)
    ):
        return await (await seva_service(request)).worker_profile(worker_id, body, actor)

    @router.get("/workers")
    async def workers(
        request: Request,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=50),
        status: str | None = None,
        actor=Depends(current_actor),
    ):
        reviewer(actor)
        service = await seva_service(request)
        query = {"verification_status": status} if status else {}
        rows = (
            await service.store.workers.find(query, {"_id": 0})
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(limit)
        )
        return {
            "items": [service.worker_view(w) for w in rows],
            "total": await service.store.workers.count_documents(query),
            "page": page,
            "limit": limit,
        }

    @router.get("/workers/{worker_id}")
    async def worker(worker_id: str, request: Request, actor=Depends(current_actor)):
        if actor.id != worker_id:
            reviewer(actor)
        service = await seva_service(request)
        record = await service.store.worker(worker_id)
        if not record:
            raise HTTPException(404, "Worker profile not found.")
        return service.worker_view(record)

    @router.post("/workers/{worker_id}/verification")
    async def verify(
        worker_id: str, body: WorkerVerification, request: Request, actor=Depends(current_actor)
    ):
        return await (await seva_service(request)).verify_worker(worker_id, body, actor)

    @router.post("/workers/{worker_id}/availability")
    async def available(
        worker_id: str, body: Availability, request: Request, actor=Depends(current_actor)
    ):
        return await (await seva_service(request)).availability(worker_id, body, actor)

    @router.post("/organizations", status_code=201)
    async def organization(body: OrganizationInput, request: Request, actor=Depends(current_actor)):
        if actor.role != UserRole.admin or body.verified_internally and not body.confirmed:
            raise HTTPException(403, "Administrator confirmation is required.")
        service = await seva_service(request)
        record = {
            **body.model_dump(),
            "id": new_id(),
            "reviewed_by": actor.id,
            "reviewed_at": now_utc(),
        }
        await service.store.db.seva_organizations.insert_one(record.copy())
        return record

    @router.get("/organizations")
    async def organizations(request: Request, actor=Depends(current_actor)):
        if actor.role not in {UserRole.admin, UserRole.coordinator, UserRole.worker}:
            raise HTTPException(403, "Staff only.")
        service = await seva_service(request)
        return await service.store.db.seva_organizations.find({"active": True}, {"_id": 0}).to_list(
            100
        )

    @router.post("/requests/{booking_id}/notifications/{notification_id}/acknowledge")
    async def acknowledge(
        booking_id: str,
        notification_id: str,
        body: Change,
        request: Request,
        idempotency_key: str = Header(default=""),
        actor=Depends(current_actor),
    ):
        service = await seva_service(request)

        async def change(booking):
            notice = next(
                (
                    n
                    for n in booking["notifications"]
                    if n["id"] == notification_id and n["delivered_at"]
                ),
                None,
            )
            if not notice:
                raise HTTPException(404, "Notification not found.")
            if actor.id not in notice["acknowledged_by"]:
                notice["acknowledged_by"].append(actor.id)

        return service.view(
            await service.mutate(
                booking_id, actor, body, idempotency_key, "notification_ack", change
            ),
            actor,
        )

    return router
