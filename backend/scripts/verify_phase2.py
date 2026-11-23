"""Real Mongo + Chroma + local ONNX API smoke test. No LLM credentials or calls.

Run after ingesting sources/pm-kisan-portal.json. Uses the configured local knowledge
base; creates fictional profile conversations and removes those records afterward.
"""

import asyncio
import secrets

from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

from app.config import Settings
from app.main import create_app


def main():
    settings = Settings(
        enable_ai=True,
        enable_dev_case_access=True,
        dev_access_token=secrets.token_urlsafe(32),
        llm_provider="none",
    )
    headers = {"X-Dev-Token": settings.dev_access_token, "X-Session-Key": secrets.token_hex(32)}
    conversations = []

    async def cleanup():
        async with AsyncMongoClient(settings.mongodb_uri) as mongo:
            await mongo[settings.mongodb_database].ai_conversations.delete_many(
                {"id": {"$in": conversations}}
            )

    try:
        with TestClient(create_app(settings)) as client:
            sources = client.get("/api/ai/schemes/pm-kisan/sources")
            assert sources.status_code == 200 and sources.json(), sources.text
            response = client.post(
                "/api/ai/scheme-match",
                headers=headers,
                json={
                    "question": "I am a farmer from Telangana. What PM KISAN support may help?",
                },
            )
            assert response.status_code == 200, response.text
            body = response.json()
            conversations.append(body["conversation_id"])
            assert body["recommendations"], body
            assert body["mode"] == "evidence-only RAG (no LLM)"
            assert all(r["evidence"] for r in body["recommendations"])
            for age in (55, 56):
                follow = client.post(
                    "/api/ai/scheme-chat",
                    headers=headers,
                    json={
                        "question": f"I am {age} years old",
                        "conversation_id": body["conversation_id"],
                    },
                )
                assert follow.status_code == 200, follow.text
                assert follow.json()["profile"]["age"] == age
                assert follow.json()["profile"]["state"] == "Telangana"
            wrong_owner = client.post(
                "/api/ai/scheme-chat",
                headers={
                    **headers,
                    "X-Session-Key": secrets.token_hex(32),
                },
                json={"question": "What support?", "conversation_id": body["conversation_id"]},
            )
            assert wrong_owner.status_code == 404
            print("PASS: official-source retrieval, citation-backed response, follow-up memory,")
            print("profile correction and session isolation; local 384-d ONNX embeddings.")
            print("Statuses:", [r["status"] for r in body["recommendations"]])
            print("Graph:", " -> ".join(body["trace"]))
            print("LLM: not configured or called; no paid API.")
    finally:
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
