import asyncio
import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.cases.models import Actor, Login


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
    if not user or not user.get("active", False):
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
        await self.database.sessions.insert_one(
            {"token_hash": hashed, "user_id": user_id, "expires_at": expiry}
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
        }

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
