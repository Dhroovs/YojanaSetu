from datetime import datetime, timedelta, timezone

from app.ai.models import Profile, SourceRecord


class KnowledgeStore:
    def __init__(self, database):
        self.database = database

    async def initialize(self):
        await self.database.ai_sources.create_index("source_id", unique=True)
        await self.database.ai_source_versions.create_index(
            [("source_id", 1), ("index_version", 1)], unique=True
        )
        await self.database.ai_conversations.create_index("id", unique=True)
        await self.database.ai_conversations.create_index("expires_at", expireAfterSeconds=0)

    async def source(self, source_id: str):
        data = await self.database.ai_sources.find_one({"source_id": source_id}, {"_id": 0})
        return SourceRecord.model_validate(data) if data else None

    async def sources(self, scheme_id: str):
        records = await self.database.ai_sources.find(
            {"scheme_id": scheme_id, "verification_status": "verified"}, {"_id": 0}
        ).to_list(100)
        return [SourceRecord.model_validate(r) for r in records]

    async def activate(self, source: SourceRecord, scheme: dict):
        # Retrieval checks the active source version before returning chunks.
        await self.database.ai_source_versions.update_one(
            {"source_id": source.source_id, "index_version": source.index_version},
            {"$setOnInsert": source.model_dump(mode="json")},
            upsert=True,
        )
        await self.database.ai_sources.replace_one(
            {"source_id": source.source_id}, source.model_dump(mode="json"), upsert=True
        )
        if source.verification_status == "verified":
            existing = await self.database.ai_sources.find(
                {"scheme_id": source.scheme_id, "verification_status": "verified"}, {"source_id": 1}
            ).to_list(100)
            scheme["source_references"] = sorted(
                {s["source_id"] for s in existing} | {source.source_id}
            )
            if len(scheme["source_references"]) > 1:
                scheme["information_completeness"] = "needs_reconciliation"
                scheme["summary"] = (
                    "Multiple official sources require reconciliation; review all cited documents."
                )
            await self.database.schemes.replace_one({"id": source.scheme_id}, scheme, upsert=True)

    async def conversation(self, conversation_id: str, owner: str):
        return await self.database.ai_conversations.find_one(
            {
                "id": conversation_id,
                "owner": owner,
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            },
            {"_id": 0},
        )

    async def save_conversation(
        self, conversation_id: str, owner: str, profile: Profile, scheme_ids: list[str], ttl: int
    ):
        # No raw questions, model prompts, transcripts or full answers are persisted.
        await self.database.ai_conversations.update_one(
            {"id": conversation_id, "owner": owner},
            {
                "$set": {
                    "profile": profile.model_dump(exclude_none=True),
                    "scheme_ids": scheme_ids,
                    "expires_at": datetime.now(timezone.utc) + timedelta(hours=ttl),
                }
            },
            upsert=True,
        )
