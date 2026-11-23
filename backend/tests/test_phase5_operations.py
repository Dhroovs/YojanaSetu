import asyncio
import os
from uuid import uuid4

import httpx
import pytest
from pymongo import AsyncMongoClient
from test_phase3 import synthetic_pdf
from test_phase3_mongo import live as live

from app.ai.providers import LanguageModel, begin_model_usage, model_usage
from app.cases.automation import process_due
from app.cases.models import Login, now_utc
from app.cases.notifications import CASE_MESSAGES
from app.cases.runtime import PrivateRuntime
from app.cases.storage import inspect_document
from app.config import Settings
from scripts.backup import backup, restore


def test_password_whitespace_is_not_silently_changed():
    password = "  synthetic-password-with-spaces  "
    assert Login(username="test-alias", password=password).password == password


def test_provider_usage_is_reported_only_when_supplied_and_is_task_local(monkeypatch):
    original = httpx.AsyncClient

    def handle(request):
        return httpx.Response(
            200,
            json={
                "message": {"content": '{"fact_ids":["0"]}'},
                "prompt_eval_count": 18,
                "eval_count": 6,
            },
        )

    monkeypatch.setattr(
        "app.ai.providers.httpx.AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(handle), **kw),
    )

    async def call():
        begin_model_usage()
        await LanguageModel(Settings(_env_file=None, llm_provider="ollama")).json("system", {})
        return model_usage()

    result = asyncio.run(call())
    assert result[0]["input_tokens"] == 18 and result[0]["output_tokens"] == 6
    assert result[0]["provider_reported"] and result[0]["estimated_cost"] is None
    assert model_usage() == []


def test_optional_ocr_failure_preserves_human_review(monkeypatch):
    import pymupdf

    def unavailable(*args, **kwargs):
        raise RuntimeError("Synthetic unavailable OCR engine")

    monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", unavailable)
    result = inspect_document(
        synthetic_pdf(text=False),
        "application/pdf",
        Settings(_env_file=None, enable_document_ocr=True),
    )
    assert result[3] == "needs_human_review"
    assert any("OCR unavailable" in note for note in result[4])


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_durable_case_notices_localize_respect_preferences_and_acknowledge(live):
    c, h, settings = live
    case = c.post(
        "/api/cases",
        headers={**h["citizen-a"], "Idempotency-Key": str(uuid4())},
        json={"scheme_id": "test-source-scheme", "assistance_type": "Synthetic assistance"},
    ).json()
    response = c.post(
        f"/api/cases/{case['id']}/preferences?revision={case['revision']}",
        headers={**h["citizen-a"], "Idempotency-Key": str(uuid4())},
        json={"in_app": True, "quiet_start": 0, "quiet_end": 0, "language": "te"},
    )
    assert response.status_code == 200, response.text

    async def sweep():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            runtime = PrivateRuntime(mongo[settings.mongodb_database], settings)
            now = now_utc()
            await process_due(runtime.cases, now)
            result = await runtime.store.load(case["id"])
            delivered = [n for n in result.notices if n.delivered_at]
            assert len(delivered) == 1 and delivered[0].message == CASE_MESSAGES["te"]
            await process_due(runtime.cases, now)
            result = await runtime.store.load(case["id"])
            assert len([n for n in result.notices if n.delivered_at]) == 1
            return result, delivered[0]

    result, notice = asyncio.run(sweep())
    path = f"/api/cases/{case['id']}/notices/{notice.id}/acknowledge"
    body = {"revision": result.revision, "note": ""}
    assert (
        c.post(
            path, headers={**h["citizen-b"], "Idempotency-Key": str(uuid4())}, json=body
        ).status_code
        == 404
    )
    response = c.post(path, headers={**h["citizen-a"], "Idempotency-Key": str(uuid4())}, json=body)
    assert response.status_code == 200, response.text
    assert "citizen-a" in response.json()["notices"][0]["acknowledged_by"]


@pytest.mark.skipif(not os.getenv("MONGO_TEST_URI"), reason="Set MONGO_TEST_URI")
def test_backup_restore_preserves_synthetic_records_indexes_and_files_without_sessions(
    live, tmp_path
):
    _, _, settings = live
    destination = "yojanasetu_restore_test_" + uuid4().hex
    private, vectors = tmp_path / "private", tmp_path / "vectors"
    private.mkdir()
    vectors.mkdir()
    (private / "synthetic.txt").write_text("Synthetic document", encoding="utf-8")
    (vectors / "synthetic-index.txt").write_text(
        "Synthetic vector storage fixture", encoding="utf-8"
    )

    async def check():
        async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
            try:
                original = mongo[settings.mongodb_database]
                await original.users.create_index("username", unique=True)
                report = await backup(original, tmp_path / "backup", private, vectors)
                assert "sessions" not in report["collections"]
                await restore(mongo[destination], tmp_path / "backup", tmp_path / "restored-files")
                assert await mongo[destination].users.count_documents({}) == 6
                assert (await mongo[destination].users.index_information())["username_1"]["unique"]
                assert await mongo[destination].sessions.count_documents({}) == 0
                assert (
                    tmp_path / "restored-files/private-documents/synthetic.txt"
                ).read_text() == "Synthetic document"
                with pytest.raises(ValueError, match="new"):
                    await restore(mongo[destination], tmp_path / "backup", tmp_path / "other-root")
            finally:
                await mongo.drop_database(destination)

    asyncio.run(check())
