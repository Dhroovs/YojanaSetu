import asyncio

from app.auth import private_runtime
from app.seva.service import SevaService
from app.seva.store import SevaStore


async def seva_service(request):
    if not hasattr(request.app.state, "seva_lock"):
        request.app.state.seva_lock = asyncio.Lock()
    async with request.app.state.seva_lock:
        if not getattr(request.app.state, "seva_service", None):
            private = await private_runtime(request)
            store = SevaStore(private.store.database)
            await store.initialize()
            request.app.state.seva_service = SevaService(
                store, private.cases, private.auth, request.app.state.settings
            )
    return request.app.state.seva_service
