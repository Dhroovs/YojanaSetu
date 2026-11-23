"""Role-safe account operations; no secret configuration or citizen documents are returned."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import current_actor, private_runtime
from app.cases.models import Change, UserRole, now_utc


class UserChange(Change):
    role: UserRole
    active: bool
    confirmed: bool


async def administrator(actor=Depends(current_actor)):
    if actor.role != UserRole.admin:
        raise HTTPException(403, "Administrator access is required.")
    return actor


def make_admin_router():
    router = APIRouter(
        prefix="/api/admin", tags=["Administration"], dependencies=[Depends(administrator)]
    )

    @router.get("/users")
    async def users(
        request: Request, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=50)
    ):
        db = (await private_runtime(request)).auth.database
        projection = {"_id": 0, "id": 1, "username": 1, "role": 1, "active": 1, "revision": 1}
        rows = (
            await db.users.find({}, projection)
            .sort("username", 1)
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(limit)
        )
        return {
            "items": [{"revision": 0, **r} for r in rows],
            "total": await db.users.count_documents({}),
            "page": page,
            "limit": limit,
        }

    @router.post("/users/{user_id}")
    async def update(
        user_id: str, body: UserChange, request: Request, actor=Depends(administrator)
    ):
        runtime = await private_runtime(request)
        target = await runtime.auth.user_by_id(user_id)
        if not target:
            raise HTTPException(404, "Account not found.")
        if target.get("revision", 0) != body.revision:
            raise HTTPException(409, "Account changed; refresh before retrying.")
        if not body.confirmed or not body.note:
            raise HTTPException(422, "Confirm the account change with an audit note.")
        # No parallel cross-demotion can remove the last administrators.
        if target["role"] == "admin":
            raise HTTPException(
                409,
                "Administrator accounts need operator-controlled changes; demotion is disabled.",
            )
        db = runtime.auth.database
        if body.role != target["role"]:
            has_visit = await db.seva_requests.find_one(
                {
                    "$or": [{"worker_id": user_id}, {"coordinator_id": user_id}],
                    "stage": {
                        "$nin": [
                            "closed",
                            "cancelled",
                            "rejected",
                            "visit_completed",
                            "follow_up_required",
                        ]
                    },
                }
            )
            has_case = await db.assistance_cases.find_one(
                {
                    "$or": [{"worker_ids": user_id}, {"coordinator_id": user_id}],
                    "stage": {"$nin": ["closed", "completed"]},
                }
            )
            if has_visit or has_case:
                raise HTTPException(
                    409, "Reassign active cases and visits before changing this role."
                )
            await db.seva_workers.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "verification_status": "pending_verification",
                        "verification_expires_at": None,
                        "active": False,
                        "account_role": body.role.value,
                    },
                    "$inc": {"revision": 1},
                },
            )
        query = {"id": user_id, "revision": body.revision}
        if body.revision == 0:
            query = {"id": user_id, "$or": [{"revision": 0}, {"revision": {"$exists": False}}]}
        result = await db.users.update_one(
            query,
            {
                "$set": {"role": body.role.value, "active": body.active},
                "$inc": {"revision": 1, "auth_version": 1},
                "$push": {
                    "administrative_audit": {
                        "actor_id": actor.id,
                        "at": now_utc(),
                        "note": body.note,
                        "role": body.role.value,
                        "active": body.active,
                    }
                },
            },
        )
        if not result.matched_count:
            raise HTTPException(409, "Account changed; refresh before retrying.")
        await db.sessions.delete_many({"user_id": user_id})
        return {
            "id": user_id,
            "role": body.role,
            "active": body.active,
            "revision": body.revision + 1,
        }

    @router.get("/operations")
    async def operations(request: Request):
        db = (await private_runtime(request)).auth.database
        await db.command("ping")
        settings = request.app.state.settings
        return {
            "database": "reachable",
            "environment": settings.app_env,
            "llm_provider": settings.llm_provider,
            "hosted_enabled": settings.allow_hosted_llm,
            "registration_enabled": settings.enable_citizen_registration,
            "ai_enabled": settings.enable_ai,
            "configuration_source": "operator environment; no secrets exposed",
            "due_case_jobs": await db.assistance_cases.count_documents(
                {"next_automation_at": {"$lte": now_utc()}}
            ),
            "due_visit_jobs": await db.seva_requests.count_documents(
                {"next_automation_at": {"$lte": now_utc()}}
            ),
        }

    return router
