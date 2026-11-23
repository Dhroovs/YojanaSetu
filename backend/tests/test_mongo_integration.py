"""Opt-in real MongoDB test. Uses a fresh database and removes only that database."""

import asyncio
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

from app.config import Settings
from app.main import create_app


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI for real MongoDB")
def test_mongo_persists_across_application_restarts():
    uri = os.environ["MONGO_TEST_URI"]
    database = f"yojanasetu_test_{uuid4().hex}"
    token = uuid4().hex
    settings = Settings(
        _env_file=None,
        mongodb_uri=uri,
        mongodb_database=database,
        app_env="development",
        enable_demo_data=True,
        enable_dev_case_access=True,
        dev_access_token=token,
    )
    headers = {"X-Dev-Token": token}

    async def inspect_and_cleanup(request_id):
        async with AsyncMongoClient(uri, serverSelectionTimeoutMS=3000) as mongo:
            try:
                assert await mongo[database].schemes.count_documents({}) == 3
                assert await mongo[database].doorstep_requests.find_one({"id": request_id})
                for name in ("schemes", "cases", "doorstep_requests"):
                    indexes = await mongo[database][name].index_information()
                    assert indexes["id_1"]["unique"] is True
            finally:
                await mongo.drop_database(database)

    request_id = None
    try:
        with TestClient(create_app(settings)) as c:
            assert c.get("/api/health").status_code == 200
            assert len(c.get("/api/schemes").json()) == 3
            assert len(c.get("/api/schemes?q=materials").json()) == 1
            assert c.get("/api/schemes?q=.*").json() == []
            assert c.get("/api/schemes/missing").status_code == 404
            assert c.get("/api/schemes", params={"q": "x" * 101}).status_code == 422
            scheme = c.get("/api/schemes?q=education").json()[0]
            assert c.get(f"/api/schemes/{scheme['id']}").status_code == 200
            case = c.post(
                "/api/cases",
                headers=headers,
                json={
                    "scheme_id": scheme["id"],
                    "assistance_type": "Guidance",
                },
            )
            assert case.status_code == 201
            case = case.json()
            doorstep = c.post(
                "/api/doorstep-requests",
                headers=headers,
                json={
                    "district": "Demo district",
                    "service_type": "Guidance",
                    "preferred_date": "2099-01-01",
                },
            )
            assert doorstep.status_code == 201
            request_id = doorstep.json()["id"]
        # A fresh app opens a fresh Mongo client; seeding must remain idempotent.
        with TestClient(create_app(settings)) as c:
            assert c.get(f"/api/cases/{case['id']}", headers=headers).json() == case
    finally:
        asyncio.run(inspect_and_cleanup(request_id))
