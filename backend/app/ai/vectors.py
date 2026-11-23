import hashlib

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.ai.models import Chunk
from app.ai.providers import Embeddings


class VectorIndex:
    def __init__(self, path: str, name: str, embeddings: Embeddings):
        self.embeddings = embeddings
        self.client = chromadb.PersistentClient(
            path=path, settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name,
            embedding_function=None,
            metadata={"embedding_identity": embeddings.identity, "hnsw:space": "cosine"},
        )
        if self.collection.metadata.get("embedding_identity") != embeddings.identity:
            raise ValueError("Embedding model changed. Use a new collection and re-ingest sources.")

    def upsert(self, chunks: list[Chunk]):
        for offset in range(0, len(chunks), 32):
            batch = chunks[offset : offset + 32]
            self.collection.upsert(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                embeddings=self.embeddings.embed([c.text for c in batch]),
                metadatas=[
                    {
                        k: v
                        for k, v in c.model_dump().items()
                        if k not in {"text", "id"} and v is not None
                    }
                    for c in batch
                ],
            )

    def remove_old(self, source_id: str, version: str):
        self.collection.delete(
            where={
                "$and": [
                    {"source_id": source_id},
                    {"index_version": {"$ne": version}},
                ]
            }
        )

    def query(self, text: str, top_k: int, max_distance: float, synthetic=False, scope=None):
        if not self.collection.count():
            return []
        verification = {"verification_status": "synthetic" if synthetic else "verified"}
        where = {"$and": [verification, {"scope": scope}]} if scope else verification
        result = self.collection.query(
            query_embeddings=self.embeddings.embed([text]),
            n_results=min(top_k, self.collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return [
            Chunk(
                id=record_id,
                text=document,
                page=None,
                **{k: v for k, v in metadata.items() if k != "page"},
            ).model_copy(update={"page": metadata.get("page")})
            for record_id, document, metadata, distance in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
                strict=True,
            )
            if distance <= max_distance
        ]

    def source_chunks(self, source_id: str, version: str) -> list[Chunk]:
        result = self.collection.get(
            where={
                "$and": [
                    {"source_id": source_id},
                    {"index_version": version},
                ]
            },
            include=["documents", "metadatas"],
        )
        return [
            Chunk(id=record_id, text=text, **{"page": None, **metadata})
            for record_id, text, metadata in zip(
                result["ids"], result["documents"], result["metadatas"], strict=True
            )
        ]


def index_version(content_hash: str, manifest_json: str, embedding_identity: str) -> str:
    # Metadata/rule/chunking changes also require reindexing, even with identical PDF bytes.
    value = f"chunk-v1:{content_hash}:{manifest_json}:{embedding_identity}"
    return hashlib.sha256(value.encode()).hexdigest()
