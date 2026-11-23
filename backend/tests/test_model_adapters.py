import asyncio

import httpx
import pytest

from app.ai.providers import EmbeddingProvider, LanguageModel, ProviderUnavailable
from app.config import Settings


@pytest.mark.parametrize(
    "provider,path", [("ollama", "/api/chat"), ("openai_compatible", "/chat/completions")]
)
def test_model_json_protocols(monkeypatch, provider, path):
    original = httpx.AsyncClient
    calls = []

    def handle(request):
        calls.append(request)
        if provider == "ollama":
            return httpx.Response(200, json={"message": {"content": '{"chunk_ids": ["a"]}'}})
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"chunk_ids": ["a"]}'}}]}
        )

    monkeypatch.setattr(
        "app.ai.providers.httpx.AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(handle), **kw),
    )
    model = LanguageModel(Settings(_env_file=None, llm_provider=provider, allow_hosted_llm=True))
    assert asyncio.run(model.json("System instruction", {"question": "untrusted"})) == {
        "chunk_ids": ["a"]
    }
    assert calls[0].url.path == path
    assert b'"role":"system"' in calls[0].content


def test_invalid_model_output_is_not_accepted(monkeypatch):
    original = httpx.AsyncClient
    transport = httpx.MockTransport(
        lambda r: httpx.Response(200, json={"message": {"content": "I approve this application"}})
    )
    monkeypatch.setattr(
        "app.ai.providers.httpx.AsyncClient", lambda **kw: original(transport=transport, **kw)
    )
    with pytest.raises(ProviderUnavailable):
        asyncio.run(
            LanguageModel(Settings(_env_file=None, llm_provider="ollama")).json("system", {})
        )


def test_ollama_embedding_protocol(monkeypatch):
    original = httpx.Client

    def handle(request):
        assert request.url.path == "/api/embed"
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})

    monkeypatch.setattr(
        "app.ai.providers.httpx.Client",
        lambda **kw: original(transport=httpx.MockTransport(handle), **kw),
    )
    assert EmbeddingProvider(
        Settings(_env_file=None, embedding_provider="ollama", embedding_model="test-model")
    ).embed(["example"]) == [[0.1, 0.2]]
