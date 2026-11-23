"""Local administrative ingestion. There is intentionally no public ingestion endpoint."""

import argparse
import asyncio
import json
import logging
from pathlib import Path

from pymongo import AsyncMongoClient

from app.ai.ingestion import download, ingest
from app.ai.models import SourceManifest
from app.ai.providers import EmbeddingProvider
from app.ai.store import KnowledgeStore
from app.ai.vectors import VectorIndex
from app.config import Settings


async def run(args):
    settings = Settings()
    if not args.confirm_reviewed:
        raise ValueError("Review document provenance/content and pass --confirm-reviewed")
    manifest = SourceManifest.model_validate_json(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest.verification_status == "synthetic":
        raise ValueError(
            "CLI accepts official reviewed sources only. Synthetic data belongs in tests."
        )
    if args.file:
        path = Path(args.file)
        if path.stat().st_size > settings.ingestion_max_bytes:
            raise ValueError("File exceeds ingestion size limit")
        data, kind = path.read_bytes(), args.kind
    else:
        data, kind = await asyncio.to_thread(
            download, str(manifest.official_url), settings.ingestion_max_bytes
        )
    index = await asyncio.to_thread(
        VectorIndex, settings.chroma_path, settings.chroma_collection, EmbeddingProvider(settings)
    )
    async with AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000) as mongo:
        store = KnowledgeStore(mongo[settings.mongodb_database])
        await store.initialize()
        # Ingestion is an offline operator operation; do not run against a serving writer.
        result = await ingest(manifest, data, kind, store, index, settings)
        print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description="Ingest a manually reviewed government source")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--file", help="Reviewed local PDF/HTML; otherwise download official URL")
    parser.add_argument("--kind", choices=["pdf", "html"], default="pdf")
    parser.add_argument("--confirm-reviewed", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        asyncio.run(run(args))
    except Exception as exc:
        logging.error("Ingestion failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
