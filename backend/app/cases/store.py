from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.cases.models import AssistanceCase, UserRole


def stored_case(case: AssistanceCase):
    data = case.model_dump(mode="python")
    data.update(
        operations=case.operations,
        creation_key=case.creation_key,
        creation_fingerprint=case.creation_fingerprint,
    )
    for raw, document in zip(data["documents"], case.documents, strict=True):
        raw["storage_key"] = document.storage_key
    return data


def actor_filter(actor):
    if actor.role == UserRole.admin:
        return {}
    if actor.role == UserRole.citizen:
        return {"owner_id": actor.id}
    if actor.role == UserRole.coordinator:
        return {"coordinator_id": actor.id}
    return {"worker_ids": actor.id}


class CaseStore:
    def __init__(self, database):
        self.database = database
        self.collection = database.assistance_cases

    async def initialize(self):
        await self.collection.create_index("id", unique=True)
        await self.collection.create_index([("owner_id", 1), ("creation_key", 1)], unique=True)
        for key in ("owner_id", "coordinator_id", "worker_ids", "next_automation_at"):
            await self.collection.create_index(key)

    async def load(self, case_id):
        data = await self.collection.find_one({"id": case_id}, {"_id": 0})
        return AssistanceCase.model_validate(data) if data else None

    async def create(self, case):
        try:
            await self.collection.insert_one(stored_case(case))
            return case
        except DuplicateKeyError:
            data = await self.collection.find_one(
                {"owner_id": case.owner_id, "creation_key": case.creation_key}, {"_id": 0}
            )
            existing = AssistanceCase.model_validate(data)
            if existing.creation_fingerprint != case.creation_fingerprint:
                raise HTTPException(409, "Idempotency key was reused with different case details.")
            return existing

    async def save(self, case, previous_revision):
        result = await self.collection.replace_one(
            {"id": case.id, "revision": previous_revision}, stored_case(case)
        )
        if not result.matched_count:
            raise HTTPException(409, "Case changed. Refresh before retrying your action.")

    async def page(self, actor, page, limit, kind="cases", stage=None):
        query = {**actor_filter(actor), "retention_purging": {"$ne": True}}
        if stage:
            query = {**query, "stage": stage}
        if kind == "reviews":
            query["documents"] = {
                "$elemMatch": {"review_status": "needs_human_review", "deleted_at": None}
            }
        elif kind == "followups":
            query["followups"] = {"$elemMatch": {"status": "scheduled"}}
        elif kind == "escalations":
            query["escalations"] = {"$elemMatch": {"status": {"$ne": "resolved"}}}
        total = await self.collection.count_documents(query)
        records = (
            await self.collection.find(query, {"_id": 0})
            .sort("updated_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(limit)
        )
        return {
            "items": [AssistanceCase.model_validate(r) for r in records],
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def unassigned(self, page, limit):
        query = {"coordinator_id": None, "stage": {"$nin": ["completed", "closed"]}}
        records = (
            await self.collection.find(
                query,
                {"_id": 0, "id": 1, "scheme_id": 1, "stage": 1, "revision": 1, "created_at": 1},
            )
            .sort("created_at", 1)
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(limit)
        )
        return {
            "items": records,
            "total": await self.collection.count_documents(query),
            "page": page,
            "limit": limit,
        }

    async def due_cases(self, now, limit):
        rows = (
            await self.collection.find(
                {
                    "next_automation_at": {"$lte": now},
                    "$or": [
                        {"stage": {"$nin": ["completed", "closed"]}},
                        {"notices": {"$elemMatch": {"delivered_at": None}}},
                    ],
                },
                {"_id": 0},
            )
            .sort("next_automation_at", 1)
            .limit(limit)
            .to_list(limit)
        )
        return [AssistanceCase.model_validate(r) for r in rows]
