import argparse
import asyncio
import logging
import signal

from pymongo import AsyncMongoClient

from app.cases.automation import process_due, purge_expired
from app.cases.runtime import PrivateRuntime
from app.config import Settings
from app.seva.automation import process_due as process_seva_due
from app.seva.service import SevaService
from app.seva.store import SevaStore


async def run(args):
    settings = Settings()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(name, stop.set)
        except NotImplementedError:
            signal.signal(name, lambda *_: loop.call_soon_threadsafe(stop.set))
    async with AsyncMongoClient(
        settings.mongodb_uri, serverSelectionTimeoutMS=3000, tz_aware=True
    ) as client:
        runtime = PrivateRuntime(client[settings.mongodb_database], settings)
        await runtime.initialize()
        seva_store = SevaStore(client[settings.mongodb_database])
        await seva_store.initialize()
        seva = SevaService(seva_store, runtime.cases, runtime.auth, settings)
        while not stop.is_set():
            try:
                count = await process_due(runtime.cases, limit=args.limit)
                visits = await process_seva_due(seva, limit=args.limit)
                purged = (
                    await purge_expired(runtime.cases, limit=args.limit)
                    if args.purge_expired
                    else 0
                )
                logging.info(
                    "Durable case sweep processed=%s retention_processed=%s visits=%s",
                    count,
                    purged,
                    visits,
                )
            except Exception as exc:
                logging.error(
                    "Worker sweep failed (%s); durable jobs remain for retry", type(exc).__name__
                )
                if args.once:
                    raise SystemExit(1) from exc
            if args.once:
                return
            try:
                await asyncio.wait_for(stop.wait(), timeout=args.poll_seconds)
            except TimeoutError:
                pass


def main():
    parser = argparse.ArgumentParser(description="Mongo-backed in-app reminder/escalation worker")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--purge-expired", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if not 5 <= args.poll_seconds <= 3600 or not 1 <= args.limit <= 500:
        parser.error("poll-seconds must be 5–3600 and limit 1–500")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
