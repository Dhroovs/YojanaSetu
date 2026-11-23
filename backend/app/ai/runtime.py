import asyncio

from fastapi import HTTPException


async def matcher_service(request):
    settings = request.app.state.settings
    if not settings.enable_ai:
        raise HTTPException(503, "Scheme assistant is disabled in local configuration.")
    if request.app.state.ai_service is None:
        async with request.app.state.ai_initialization_lock:
            if request.app.state.ai_service is None:
                from app.agents.scheme_matcher import SchemeMatcher
                from app.ai.providers import EmbeddingProvider, LanguageModel
                from app.ai.service import MatcherService
                from app.ai.store import KnowledgeStore
                from app.ai.vectors import VectorIndex

                store = KnowledgeStore(request.app.state.repository.database)
                await store.initialize()
                settings = request.app.state.settings
                index = await asyncio.to_thread(
                    VectorIndex,
                    settings.chroma_path,
                    settings.chroma_collection,
                    EmbeddingProvider(settings),
                )
                request.app.state.ai_service = MatcherService(
                    store, SchemeMatcher(store, index, LanguageModel(settings), settings), settings
                )
    return request.app.state.ai_service
