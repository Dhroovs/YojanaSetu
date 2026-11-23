from fastapi import HTTPException
from pymongo import ReturnDocument


class SevaStore:
    def __init__(self, database):
        self.db = database
        self.bookings, self.workers = database.seva_requests, database.seva_workers

    async def initialize(self):
        await self.bookings.create_index("id", unique=True)
        await self.bookings.create_index([("owner_id", 1), ("creation_key", 1)], unique=True)
        for key in ("owner_id", "worker_id", "coordinator_id", "stage", "next_automation_at"):
            await self.bookings.create_index(key)
        await self.workers.create_index("id", unique=True)
        await self.db.seva_organizations.create_index("id", unique=True)

    async def booking(self, booking_id):
        return await self.bookings.find_one({"id": booking_id}, {"_id": 0})

    async def worker(self, worker_id):
        return await self.workers.find_one({"id": worker_id}, {"_id": 0})

    async def save(self, booking, revision):
        result = await self.bookings.replace_one(
            {"id": booking["id"], "revision": revision}, booking
        )
        if not result.matched_count:
            raise HTTPException(409, "Request changed. Refresh before retrying.")

    async def reserve(self, worker, booking_id, window, now, expected_booking_revision):
        # One atomic calendar document is the conflict authority, even on standalone MongoDB.
        query = {
            "id": worker["id"],
            "revision": worker["revision"],
            "active": True,
            "verification_status": {"$in": ["verified_internally", "authorization_confirmed"]},
            "verification_expires_at": {"$gt": window.end},
            "reservations": {
                "$not": {"$elemMatch": {"start": {"$lt": window.end}, "end": {"$gt": window.start}}}
            },
            "$expr": {
                "$lt": [
                    {
                        "$size": {
                            "$filter": {
                                "input": "$reservations",
                                "as": "r",
                                "cond": {"$gt": ["$$r.end", now]},
                            }
                        }
                    },
                    worker["capacity"],
                ]
            },
        }
        reservation = {
            "booking_id": booking_id,
            "start": window.start,
            "end": window.end,
            "accepted": False,
            "expected_booking_revision": expected_booking_revision,
        }
        result = await self.workers.find_one_and_update(
            query,
            {"$push": {"reservations": reservation}, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise HTTPException(
                409, "Worker calendar, verification or capacity changed. Refresh the shortlist."
            )

    async def release(self, worker_id, booking_id):
        if worker_id:
            await self.workers.update_one(
                {"id": worker_id},
                {"$pull": {"reservations": {"booking_id": booking_id}}, "$inc": {"revision": 1}},
            )
