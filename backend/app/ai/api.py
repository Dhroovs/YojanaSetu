import asyncio
import logging
import re
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.ai.models import MatchRequest, MatchResponse, SourceRecord
from app.ai.providers import ProviderUnavailable

logger = logging.getLogger(__name__)


def make_router(settings, dev_access):
    router = APIRouter(prefix="/api/ai", tags=["Scheme Matcher"])
    initialization = asyncio.Lock()
    hits = defaultdict(deque)

    async def service(request: Request):
        if not settings.enable_ai:
            raise HTTPException(
                503, "Scheme assistant disabled. Enable AI and configure the knowledge base."
            )
        if getattr(request.app.state, "ai_service", None) is None:
            async with initialization:
                if getattr(request.app.state, "ai_service", None) is None:
                    from app.agents.scheme_matcher import SchemeMatcher
                    from app.ai.providers import EmbeddingProvider, LanguageModel
                    from app.ai.service import MatcherService
                    from app.ai.store import KnowledgeStore
                    from app.ai.vectors import VectorIndex

                    store = KnowledgeStore(request.app.state.repository.database)
                    await store.initialize()
                    index = await asyncio.to_thread(
                        VectorIndex,
                        settings.chroma_path,
                        settings.chroma_collection,
                        EmbeddingProvider(settings),
                    )
                    matcher = SchemeMatcher(store, index, LanguageModel(settings), settings)
                    request.app.state.ai_service = MatcherService(store, matcher, settings)
        return request.app.state.ai_service

    async def authorize(
        request: Request, x_session_key: str = Header(default=""), _=Depends(dev_access)
    ):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{32,128}", x_session_key):
            raise HTTPException(401, "An independent browser session key is required.")
        # Per-IP admission rate, in addition to bounded in-flight matching concurrency.
        key = request.client.host if request.client else "local"
        now = time.monotonic()
        queue = hits[key]
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= settings.ai_requests_per_minute:
            raise HTTPException(
                429, "Too many requests. Please wait one minute.", headers={"Retry-After": "60"}
            )
        queue.append(now)
        return x_session_key

    async def run(body, request, session_key):
        try:
            active = await service(request)
            return await active.match(body, session_key)
        except TimeoutError as exc:
            raise HTTPException(504, "Scheme matching timed out. Please try again.") from exc
        except ProviderUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        except (ImportError, RuntimeError) as exc:
            raise HTTPException(
                503, "AI dependencies could not load. Check the local installation."
            ) from exc
        except ValueError as exc:
            logger.warning("AI configuration or index error: %s", type(exc).__name__)
            raise HTTPException(
                503, "Knowledge index configuration error. Contact the local coordinator."
            ) from exc

    @router.post("/scheme-match", response_model=MatchResponse)
    async def match(body: MatchRequest, request: Request, session_key=Depends(authorize)):
        return await run(body, request, session_key)

    @router.post("/scheme-chat", response_model=MatchResponse)
    async def chat(body: MatchRequest, request: Request, session_key=Depends(authorize)):
        return await run(body, request, session_key)

    @router.get("/coverage")
    async def coverage(request: Request):
        from app.ai.quality import coverage_report

        if not hasattr(request.app.state.repository, "database"):
            return coverage_report([])
        rows = await request.app.state.repository.database.ai_sources.find(
            {"verification_status": "verified"}, {"_id": 0}
        ).to_list(1000)
        return coverage_report(
            [SourceRecord.model_validate(r) for r in rows], settings.source_max_age_days
        )

    @router.get("/schemes/{scheme_id}/sources", response_model=list[SourceRecord])
    async def sources(scheme_id: str, request: Request):
        # Only reviewed scheme source metadata is public. No profiles or conversations.
        from app.ai.store import KnowledgeStore

        if not hasattr(request.app.state.repository, "database"):
            return []
        return await KnowledgeStore(request.app.state.repository.database).sources(scheme_id)

    return router
