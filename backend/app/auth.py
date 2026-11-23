import asyncio
import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import Field
from pymongo.errors import DuplicateKeyError

from app.cases.models import Actor, Login, Strict, new_id


class Registration(Login):
    consent: bool
    language: str = Field(default="en", pattern=r"^(en|hi|te)$")


class AccountPreferences(Strict):
    language: str = Field(pattern=r"^(en|hi|te)$")


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32, maxmem=64 * 1024 * 1024
    )
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, _ = stored.split("$")
        return scheme == "scrypt" and hmac.compare_digest(
            hash_password(password, base64.b64decode(salt)), stored
        )
    except (ValueError, TypeError):
        return False


def token_hash(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


async def private_runtime(request: Request):
    if request.app.state.private_runtime is None:
        async with request.app.state.private_initialization_lock:
            if request.app.state.private_runtime is None:
                from app.cases.runtime import PrivateRuntime

                runtime = PrivateRuntime(
                    request.app.state.repository.database, request.app.state.settings
                )
                await runtime.initialize()
                request.app.state.private_runtime = runtime
    return request.app.state.private_runtime


async def current_actor(request: Request, authorization: str = Header(default="")) -> Actor:
    if not authorization.startswith("Bearer ") or len(authorization) > 200:
        raise HTTPException(401, "Sign in to access private assistance cases.")
    runtime = await private_runtime(request)
    session = await runtime.auth.session(token_hash(authorization[7:]))
    if not session:
        raise HTTPException(401, "Session expired or revoked. Sign in again.")
    user = await runtime.auth.user_by_id(session["user_id"])
    if (
        not user
        or not user.get("active", False)
        or (user.get("demo_only") and request.app.state.settings.app_env != "development")
        or session.get("auth_version", 0) != user.get("auth_version", 0)
    ):
        raise HTTPException(401, "Session expired or revoked. Sign in again.")
    return Actor(id=user["id"], username=user["username"], role=user["role"])


class MongoAuthStore:
    def __init__(self, database):
        self.database = database

    async def initialize(self):
        await self.database.users.create_index("username", unique=True)
        await self.database.users.create_index("id", unique=True)
        await self.database.sessions.create_index("token_hash", unique=True)
        await self.database.sessions.create_index("expires_at", expireAfterSeconds=0)
        await self.database.auth_admission.create_index("expires_at", expireAfterSeconds=0)

    async def user(self, username):
        return await self.database.users.find_one({"username": username}, {"_id": 0})

    async def user_by_id(self, user_id):
        return await self.database.users.find_one({"id": user_id}, {"_id": 0})

    async def session(self, hashed):
        return await self.database.sessions.find_one(
            {"token_hash": hashed, "expires_at": {"$gt": datetime.now(timezone.utc)}}, {"_id": 0}
        )

    async def login_failure(self, user_id):
        from pymongo import ReturnDocument

        user = await self.database.users.find_one_and_update(
            {"id": user_id}, {"$inc": {"failed_logins": 1}}, return_document=ReturnDocument.AFTER
        )
        if user and user.get("failed_logins", 0) >= 5:
            await self.database.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "locked_until": datetime.now(timezone.utc) + timedelta(minutes=5),
                    }
                },
            )

    async def add_session(self, hashed, user_id, expiry):
        user = await self.user_by_id(user_id)
        await self.database.sessions.insert_one(
            {
                "token_hash": hashed,
                "user_id": user_id,
                "expires_at": expiry,
                "auth_version": user.get("auth_version", 0),
            }
        )
        await self.database.users.update_one(
            {"id": user_id}, {"$set": {"failed_logins": 0}, "$unset": {"locked_until": ""}}
        )

    async def revoke(self, hashed):
        await self.database.sessions.delete_one({"token_hash": hashed})

    async def staff(self):
        return await self.database.users.find(
            {"role": {"$in": ["worker", "coordinator", "admin"]}, "active": True},
            {"_id": 0, "id": 1, "username": 1, "role": 1},
        ).to_list(200)


def make_auth_router(settings):
    router = APIRouter(prefix="/api/auth", tags=["Authentication"])
    attempts = defaultdict(deque)
    dummy = hash_password("not-an-account-" + secrets.token_hex(16))

    @router.post("/register", status_code=201, response_model=Actor)
    async def register(body: Registration, request: Request):
        if not settings.enable_citizen_registration:
            raise HTTPException(403, "Citizen registration is disabled by the operator.")
        if not body.consent:
            raise HTTPException(422, "Confirm the privacy notice before creating an account.")
        runtime = await private_runtime(request)
        from pymongo import ReturnDocument

        now = datetime.now(timezone.utc)
        ip = request.client.host if request.client else "local"
        key = token_hash(f"registration:{ip}:{int(now.timestamp()) // 60}")
        counter = await runtime.auth.database.auth_admission.find_one_and_update(
            {"_id": key},
            {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": now + timedelta(minutes=2)}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if counter["count"] > 5:
            raise HTTPException(429, "Too many registration attempts. Wait one minute.")
        user = {
            "id": new_id(),
            "username": body.username.casefold(),
            "role": "citizen",
            "active": True,
            "password_hash": await asyncio.to_thread(hash_password, body.password),
            "revision": 0,
            "auth_version": 0,
            "language": body.language,
            "privacy_consent_at": now,
            "failed_logins": 0,
        }
        try:
            await runtime.auth.database.users.insert_one(user.copy())
        except DuplicateKeyError as exc:
            raise HTTPException(409, "Account alias is unavailable. Choose another alias.") from exc
        return Actor(id=user["id"], username=user["username"], role="citizen")

    @router.post("/login")
    async def login(body: Login, request: Request):
        key = request.client.host if request.client else "local"
        now = time.monotonic()
        queue = attempts[key]
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= settings.login_attempts_per_minute:
            raise HTTPException(
                429, "Too many sign-in attempts. Wait a minute.", headers={"Retry-After": "60"}
            )
        queue.append(now)
        runtime = await private_runtime(request)
        user = await runtime.auth.user(body.username.casefold())
        good = await asyncio.to_thread(
            verify_password, body.password, user["password_hash"] if user else dummy
        )
        locked = user and user.get("locked_until")
        if locked and locked.tzinfo is None:
            locked = locked.replace(tzinfo=timezone.utc)
        if (
            not good
            or not user
            or not user.get("active")
            or (user.get("demo_only") and settings.app_env != "development")
            or (locked and locked > datetime.now(timezone.utc))
        ):
            if user and (not locked or locked <= datetime.now(timezone.utc)):
                await runtime.auth.login_failure(user["id"])
            raise HTTPException(401, "Invalid credentials or temporarily locked account.")
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=settings.session_hours)
        await runtime.auth.add_session(token_hash(token), user["id"], expiry)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expiry,
            "user": Actor(id=user["id"], username=user["username"], role=user["role"]),
            "language": user.get("language", "en"),
        }

    @router.post("/preferences")
    async def preferences(body: AccountPreferences, request: Request, actor=Depends(current_actor)):
        runtime = await private_runtime(request)
        await runtime.auth.database.users.update_one(
            {"id": actor.id}, {"$set": {"language": body.language}}
        )
        return {"language": body.language}

    @router.get("/me", response_model=Actor)
    async def me(actor=Depends(current_actor)):
        return actor

    @router.post("/logout", status_code=204)
    async def logout(
        request: Request, authorization: str = Header(default=""), actor=Depends(current_actor)
    ):
        runtime = await private_runtime(request)
        await runtime.auth.revoke(token_hash(authorization[7:]))

    return router
