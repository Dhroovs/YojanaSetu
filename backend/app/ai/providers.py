"""No paid provider is enabled implicitly. Model outputs are always untrusted."""

import json
from typing import Protocol

import httpx

from app.config import Settings


class ProviderUnavailable(RuntimeError):
    pass


class Embeddings(Protocol):
    identity: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.identity = f"{settings.embedding_provider}:{settings.embedding_model}"
        self.local = None

    def embed(self, texts):
        try:
            if self.settings.embedding_provider == "onnx":
                if self.settings.embedding_model != "all-MiniLM-L6-v2":
                    raise ProviderUnavailable("ONNX supports all-MiniLM-L6-v2 only")
                if self.local is None:
                    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

                    self.local = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
                return [list(map(float, v)) for v in self.local(texts)]
            if self.settings.embedding_provider == "ollama":
                with httpx.Client(timeout=self.settings.model_timeout_seconds) as client:
                    response = client.post(
                        f"{self.settings.model_base_url.rstrip('/')}/api/embed",
                        json={
                            "model": self.settings.embedding_model,
                            "input": texts,
                            "truncate": False,
                        },
                    )
                    response.raise_for_status()
                    return response.json()["embeddings"]
            raise ProviderUnavailable("Unsupported embedding provider")
        except (httpx.HTTPError, ValueError, KeyError, RuntimeError) as exc:
            raise ProviderUnavailable(
                "Embedding provider unavailable; check model configuration"
            ) from exc


class LanguageModel:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = settings.llm_provider != "none"

    async def json(self, system: str, data: dict) -> dict:
        if not self.enabled:
            return {}
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
        ]
        try:
            async with httpx.AsyncClient(timeout=self.settings.model_timeout_seconds) as client:
                if self.settings.llm_provider == "ollama":
                    response = await client.post(
                        f"{self.settings.model_base_url.rstrip('/')}/api/chat",
                        json={
                            "model": self.settings.llm_model,
                            "messages": messages,
                            "stream": False,
                            "format": "json",
                            "options": {"temperature": 0},
                        },
                    )
                    response.raise_for_status()
                    content = response.json()["message"]["content"]
                elif self.settings.llm_provider == "openai_compatible":
                    response = await client.post(
                        f"{self.settings.model_base_url.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {self.settings.model_api_key}"},
                        json={
                            "model": self.settings.llm_model,
                            "messages": messages,
                            "temperature": 0,
                            "response_format": {"type": "json_object"},
                        },
                    )
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                else:
                    raise ProviderUnavailable("Unsupported LLM provider")
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError("Expected a JSON object")
            return result
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise ProviderUnavailable(
                "Language model unavailable or returned invalid JSON"
            ) from exc
