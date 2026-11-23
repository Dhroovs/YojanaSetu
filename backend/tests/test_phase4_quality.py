import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.ai.models import SourceRecord
from app.ai.providers import LanguageModel, ProviderUnavailable
from app.ai.quality import coverage_report
from app.config import Settings
from app.seva.communications import DisabledChannel


def source():
    data = json.loads(
        (Path(__file__).parents[1] / "sources/pmsby-faq.json").read_text(encoding="utf-8")
    )
    return SourceRecord(
        **data,
        retrieved_at=datetime.now(timezone.utc),
        content_hash="a" * 64,
        index_version="version-a",
        chunk_count=1,
    )


def test_coverage_detects_duplicates_conflicting_reviewed_thresholds_and_unknowns():
    one = source()
    two = one.model_copy(deep=True)
    two.source_id = "second-reviewed-source"
    two.rules[0].value = 21
    report = coverage_report([one, two])
    assert report["source_count"] == 2 and report["scheme_count"] == 1
    assert report["duplicate_content"] == [[one.source_id, two.source_id]]
    assert report["schemes"][0]["potential_conflicts"]
    assert report["schemes"][0]["requires_reconciliation"]
    assert "required_documents" in report["schemes"][0]["sources"][0]["missing_fields"]


def mock_model(monkeypatch, handler, **kwargs):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.ai.providers.httpx.AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(handler), **kw),
    )
    return LanguageModel(Settings(_env_file=None, llm_provider="ollama", **kwargs))


def test_hosted_provider_is_blocked_before_any_network_call(monkeypatch):
    monkeypatch.setattr(
        "app.ai.providers.httpx.AsyncClient", lambda **kw: pytest.fail("Unexpected network call")
    )
    with pytest.raises(ProviderUnavailable, match="disabled"):
        asyncio.run(
            LanguageModel(Settings(_env_file=None, llm_provider="openai_compatible")).json(
                "system", {}
            )
        )


def test_transient_failure_has_bounded_retry_and_token_cap(monkeypatch):
    calls = []

    def handle(request):
        calls.append(request)
        assert json.loads(request.content)["options"]["num_predict"] == 96
        return httpx.Response(503)

    model = mock_model(monkeypatch, handle, llm_retry_limit=1, llm_max_output_tokens=96)
    with pytest.raises(ProviderUnavailable):
        asyncio.run(model.json("system", {}))
    assert len(calls) == 2


def test_injection_and_unknown_fact_ids_never_become_summary_claims(monkeypatch):
    model = mock_model(
        monkeypatch,
        lambda r: httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {"fact_ids": ["999"], "claim": "Government approval granted"}
                    )
                }
            },
        ),
    )
    result = asyncio.run(model.grounded_summary(["Internal stage: pending review."]))
    assert result == {
        "facts": ["Internal stage: pending review."],
        "mode": "deterministic_fallback",
    }


def test_input_limit_blocks_request_and_oversized_output_falls_back(monkeypatch):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"message": {"content": "x" * 300}})

    model = mock_model(monkeypatch, handle, llm_max_input_chars=1000, llm_max_output_chars=256)
    with pytest.raises(ProviderUnavailable):
        asyncio.run(model.json("system", {"text": "x" * 1001}))
    assert not calls
    assert (
        asyncio.run(model.grounded_summary(["Authorized fact"]))["mode"] == "deterministic_fallback"
    )
    assert len(calls) == 1


@pytest.mark.parametrize("channel", ["sms", "whatsapp"])
def test_external_messaging_is_disabled(channel):
    with pytest.raises(RuntimeError, match="disabled"):
        asyncio.run(DisabledChannel(channel).send_template("synthetic-reference", "update", "en"))
