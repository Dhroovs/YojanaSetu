from app.auth import MongoAuthStore
from app.cases.service import CaseService
from app.cases.storage import LocalPrivateStorage
from app.cases.store import CaseStore


class PrivateRuntime:
    def __init__(self, database, settings):
        self.auth = MongoAuthStore(database)
        self.store = CaseStore(database)
        self.storage = LocalPrivateStorage(settings.document_storage_path)
        self.cases = CaseService(self.store, self.auth, self.storage, settings)

    async def initialize(self):
        await self.auth.initialize()
        await self.store.initialize()
