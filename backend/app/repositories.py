from typing import Protocol

from app.models import GovernmentScheme


class SchemeIngestionSource(Protocol):
    """Future adapters must supply verified provenance before production ingestion."""

    async def fetch(self) -> list[GovernmentScheme]: ...


class MongoRepository:
    def __init__(self, database):
        self.database = database

    async def list_schemes(self, query: str):
        # Literal substring matching avoids user-controlled Mongo regular expressions.
        records = await self.database.schemes.find({}, {"_id": 0}).to_list(length=500)
        return [
            r
            for r in records
            if query.casefold() in f"{r['title']} {r['category']} {r['summary']}".casefold()
        ]

    async def get(self, collection: str, record_id: str):
        return await self.database[collection].find_one({"id": record_id}, {"_id": 0})

    async def insert(self, collection: str, record):
        await self.database[collection].insert_one(record.model_dump(mode="json"))

    async def seed(self, schemes):
        for collection in ("schemes", "cases", "doorstep_requests"):
            await self.database[collection].create_index("id", unique=True)
        for scheme in schemes:
            await self.database.schemes.update_one(
                {"id": scheme.id}, {"$setOnInsert": scheme.model_dump()}, upsert=True
            )
