"""Verify the actual local source index and coverage API without any LLM call."""

import asyncio
import secrets

from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

from app.config import Settings
from app.main import create_app


def main():
    settings = Settings(
        enable_ai=True,
        llm_provider="none",
        allow_hosted_llm=False,
        enable_dev_case_access=True,
        dev_access_token=secrets.token_urlsafe(32),
    )
    headers = {"X-Dev-Token": settings.dev_access_token, "X-Session-Key": secrets.token_hex(32)}
    conversations = []
    try:
        with TestClient(create_app(settings)) as client:
            report = client.get("/api/ai/coverage")
            assert report.status_code == 200, report.text
            report = report.json()
            assert report["scheme_count"] == 3 and report["source_count"] >= 3
            for scheme_id, question in [
                ("pmsby", "PMSBY Pradhan Mantri Suraksha Bima Yojana accident insurance"),
                ("kalyana-lakshmi", "Telangana Kalyana Lakshmi Pathakam marriage assistance"),
            ]:
                response = client.post(
                    "/api/ai/scheme-match",
                    headers=headers,
                    json={"question": question, "profile": {"age": 30, "state": "Telangana"}},
                )
                assert response.status_code == 200, response.text
                data = response.json()
                conversations.append(data["conversation_id"])
                recommendation = next(
                    r for r in data["recommendations"] if r["scheme_id"] == scheme_id
                )
                assert recommendation["evidence"] and recommendation["completeness"] in {
                    "partial",
                    "needs_reconciliation",
                }
                assert recommendation["status"] == "Unable to determine"
                assert all(
                    e["verification_status"] == "verified" for e in recommendation["evidence"]
                )
                print(
                    f"PASS: {scheme_id} retrieval, verified citations, partial/unknown eligibility"
                )
            print("PASS: coverage API reports official sources / 3 schemes; no LLM called.")
    finally:

        async def cleanup():
            async with AsyncMongoClient(settings.mongodb_uri) as mongo:
                await mongo[settings.mongodb_database].ai_conversations.delete_many(
                    {"id": {"$in": conversations}}
                )

        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
