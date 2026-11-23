"""Operator-only quiesced backup and non-destructive restore to a NEW database/files root."""

import argparse
import asyncio
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import AsyncMongoClient

from app.config import Settings


async def backup(database, directory, private_path, chroma_path):
    directory = Path(directory).resolve()
    for location in (private_path, chroma_path):
        source = Path(location).resolve()
        if (
            directory == source
            or directory.is_relative_to(source)
            or source.is_relative_to(directory)
        ):
            raise ValueError("Backup directory must be separate from live storage")
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "format": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database": database.name,
        "collections": {},
    }
    for name in await database.list_collection_names():
        if name.startswith("system.") or name in {"sessions", "auth_admission", "seva_rate_limits"}:
            continue
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Unsupported collection name")
        path = directory / f"{name}.jsonl"
        count = 0
        with path.open("w", encoding="utf-8") as stream:
            async for row in database[name].find({}):
                stream.write(json_util.dumps(row) + "\n")
                count += 1
        manifest["collections"][name] = {
            "count": count,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "indexes": await database[name].index_information(),
        }
    for label, source in (("private-documents", private_path), ("chroma", chroma_path)):
        source = Path(source).resolve()
        if (
            directory == source
            or directory.is_relative_to(source)
            or source.is_relative_to(directory)
        ):
            raise ValueError("Backup directory must be separate from live storage")
        if source.exists():
            shutil.copytree(source, directory / label)
    (directory / "manifest.json").write_text(json_util.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


async def restore(database, directory, files_root):
    directory, files_root = Path(directory).resolve(), Path(files_root).resolve()
    manifest = json_util.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != 1 or database.name == manifest["database"]:
        raise ValueError("Restore requires supported backup and a different target database")
    if await database.list_collection_names() or files_root.exists():
        raise ValueError(
            "Restore database and files root must be new; existing data is never overwritten"
        )
    if files_root.is_relative_to(directory) or directory.is_relative_to(files_root):
        raise ValueError("Restore files must be separate from the backup")
    # Verify every collection before creating anything in the destination.
    for name, info in manifest["collections"].items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Invalid collection name")
        path = directory / f"{name}.jsonl"
        if hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
            raise ValueError("Backup collection integrity check failed")
    for name, info in manifest["collections"].items():
        for index_name, spec in info["indexes"].items():
            if index_name != "_id_":
                options = {k: v for k, v in spec.items() if k not in {"key", "v", "ns"}}
                await database[name].create_index(spec["key"], **options)
        path = directory / f"{name}.jsonl"
        batch = []
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                batch.append(json_util.loads(line))
                if len(batch) == 500:
                    await database[name].insert_many(batch)
                    batch = []
        if batch:
            await database[name].insert_many(batch)
        if await database[name].count_documents({}) != info["count"]:
            raise ValueError("Restore count mismatch; keep services stopped and investigate")
    files_root.mkdir(parents=True)
    for label in ("private-documents", "chroma"):
        if (directory / label).exists():
            shutil.copytree(directory / label, files_root / label)
    return manifest


async def run(args):
    settings = Settings()
    if not args.confirm_quiesced:
        raise ValueError("Stop API, scheduler and ingestion writers; pass --confirm-quiesced")
    async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as mongo:
        if args.mode == "backup":
            report = await backup(
                mongo[settings.mongodb_database],
                args.directory,
                settings.document_storage_path,
                settings.chroma_path,
            )
        else:
            if (
                not args.target_database
                or not args.files_root
                or args.target_database == settings.mongodb_database
            ):
                raise ValueError(
                    "Provide a NEW --target-database and --files-root; live database is forbidden"
                )
            report = await restore(mongo[args.target_database], args.directory, args.files_root)
    print(
        json.dumps(
            {
                "operation": args.mode,
                "collections": len(report["collections"]),
                "sessions_restored": False,
                "warning": "Backup contains sensitive data; encrypt and restrict access.",
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["backup", "restore"])
    parser.add_argument("directory")
    parser.add_argument("--confirm-quiesced", action="store_true")
    parser.add_argument("--target-database")
    parser.add_argument("--files-root")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
