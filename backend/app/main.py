import asyncio
import secrets
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.cases.models import AssistanceCase
from app.config import Settings
from app.demo import demo_schemes
from app.models import CaseCreate, CitizenCase, DoorstepCreate, DoorstepRequest, GovernmentScheme
from app.repositories import MongoRepository


def create_app(
    settings: Settings | None = None, repository=None, ai_service=None, private_runtime=None
):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        client = None
        if repository is None:
            client = AsyncMongoClient(
                settings.mongodb_uri, serverSelectionTimeoutMS=3000, tz_aware=True
            )
            app.state.repository = MongoRepository(client[settings.mongodb_database])
        else:
            app.state.repository = repository
        try:
            if settings.enable_demo_data and settings.app_env == "development":
                try:
                    await app.state.repository.seed(demo_schemes())
                except PyMongoError:
                    # API reports 503 while MongoDB is unavailable.
                    pass
            yield
        finally:
            if client is not None:
                await client.close()

    app = FastAPI(title="YojanaSetu · Phase 3", lifespan=lifespan)
    app.state.ai_service = ai_service
    app.state.settings = settings
    app.state.private_runtime = private_runtime
    app.state.private_initialization_lock = asyncio.Lock()
    app.state.ai_initialization_lock = asyncio.Lock()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Idempotency-Key",
            "X-Dev-Token",
            "X-Session-Key",
        ],
    )

    @app.exception_handler(PyMongoError)
    async def database_error(request: Request, exc: PyMongoError):
        return JSONResponse(
            status_code=503, content={"detail": "Database unavailable. Try again later."}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Validation responses must never echo passwords, notes or document bytes.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
                    for e in exc.errors()
                ]
            },
        )

    @app.exception_handler(TimeoutError)
    async def timeout_error(request, exc):
        return JSONResponse(
            status_code=504, content={"detail": "Assistance task timed out. Please retry."}
        )

    @app.middleware("http")
    async def private_no_cache(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(("/api/auth", "/api/cases", "/api/coordinator")):
            response.headers["Cache-Control"] = "no-store"
        return response

    def repo(request: Request):
        return request.app.state.repository

    def dev_access(x_dev_token: str = Header(default="")):
        if (
            settings.app_env != "development"
            or not settings.enable_dev_case_access
            or len(settings.dev_access_token) < 32
        ):
            raise HTTPException(403, "Case services disabled until authentication is available.")
        if not secrets.compare_digest(
            x_dev_token.encode("utf-8"), settings.dev_access_token.encode("utf-8")
        ):
            raise HTTPException(401, "A valid local development token is required.")

    from app.ai.api import make_router

    app.include_router(make_router(settings, dev_access))
    from app.auth import make_auth_router
    from app.cases.api import make_case_router

    app.include_router(make_auth_router(settings))
    app.include_router(make_case_router())

    @app.get("/api/health")
    async def health(repository=Depends(repo)):
        await repository.list_schemes("")
        return {"status": "ok", "environment": settings.app_env}

    @app.get("/api/schemes", response_model=list[GovernmentScheme])
    async def schemes(q: str = Query(default="", max_length=100), repository=Depends(repo)):
        return await repository.list_schemes(q.strip())

    @app.get("/api/schemes/{scheme_id}", response_model=GovernmentScheme)
    async def scheme(scheme_id: str, repository=Depends(repo)):
        record = await repository.get("schemes", scheme_id)
        if not record:
            raise HTTPException(404, "Scheme not found.")
        return record

    @app.post(
        "/api/cases",
        response_model=AssistanceCase | CitizenCase,
        status_code=201,
    )
    async def create_case(
        body: CaseCreate,
        request: Request,
        repository=Depends(repo),
        authorization: str = Header(default=""),
        x_dev_token: str = Header(default=""),
        idempotency_key: str = Header(default=""),
    ):
        if authorization:
            from app.auth import current_actor, private_runtime

            actor = await current_actor(request, authorization)
            runtime = await private_runtime(request)
            return await runtime.cases.create(body, actor, idempotency_key)
        dev_access(x_dev_token)
        if not await repository.get("schemes", body.scheme_id):
            raise HTTPException(404, "Scheme not found.")
        record = CitizenCase(**body.model_dump())
        await repository.insert("cases", record)
        return record

    @app.get("/api/cases/{case_id}", response_model=AssistanceCase | CitizenCase)
    async def get_case(
        case_id: str,
        request: Request,
        repository=Depends(repo),
        authorization: str = Header(default=""),
        x_dev_token: str = Header(default=""),
    ):
        if authorization:
            from app.auth import current_actor, private_runtime

            actor = await current_actor(request, authorization)
            runtime = await private_runtime(request)
            return await runtime.cases.authorized(case_id, actor)
        dev_access(x_dev_token)
        record = await repository.get("cases", case_id)
        if not record or record.get("owner_id"):
            raise HTTPException(404, "Case not found.")
        return record

    @app.post(
        "/api/doorstep-requests",
        response_model=DoorstepRequest,
        status_code=201,
        dependencies=[Depends(dev_access)],
    )
    async def doorstep(body: DoorstepCreate, repository=Depends(repo)):
        if body.preferred_date < date.today():
            raise HTTPException(422, "Preferred date must be today or later.")
        record = DoorstepRequest(**body.model_dump())
        await repository.insert("doorstep_requests", record)
        return record

    return app


app = create_app()
