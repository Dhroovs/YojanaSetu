import argparse
import asyncio
import getpass
import re
from uuid import uuid4

from pymongo import AsyncMongoClient

from app.auth import hash_password
from app.cases.runtime import PrivateRuntime
from app.config import Settings


async def run(args):
    settings = Settings()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,50}", args.username):
        raise ValueError("Use a 3–50 character account alias, not personal contact information")
    password = getpass.getpass("New password (12+ characters): ")
    if (
        len(password) < 12
        or len(password) > 128
        or password != getpass.getpass("Confirm password: ")
    ):
        raise ValueError("Passwords must match and contain 12–128 characters")
    async with AsyncMongoClient(settings.mongodb_uri, tz_aware=True) as client:
        runtime = PrivateRuntime(client[settings.mongodb_database], settings)
        await runtime.initialize()
        if await runtime.auth.user(args.username.casefold()):
            raise ValueError("Account alias already exists; no changes made")
        await client[settings.mongodb_database].users.insert_one(
            {
                "id": str(uuid4()),
                "username": args.username.casefold(),
                "role": args.role,
                "password_hash": hash_password(password),
                "active": True,
                "failed_logins": 0,
            }
        )
    print(f"Provisioned {args.role} account. No password or session token was logged.")


def main():
    parser = argparse.ArgumentParser(description="Local operator-only account provisioning")
    parser.add_argument("--username", required=True)
    parser.add_argument(
        "--role", required=True, choices=["citizen", "worker", "coordinator", "admin"]
    )
    try:
        asyncio.run(run(parser.parse_args()))
    except Exception as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
