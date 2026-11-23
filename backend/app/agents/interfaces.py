from datetime import datetime
from typing import Protocol

from app.ai.models import MatchRequest, MatchResponse
from app.cases.models import AssistanceCase


class SchemeMatcherAgent(Protocol):
    async def match(self, request: MatchRequest, session_key: str) -> MatchResponse:
        """Return structured, cited guidance; implemented by MatcherService in Phase 2."""
        ...


class DocumentVerifierAgent(Protocol):
    def analyze(self, case: AssistanceCase, now: datetime) -> dict: ...


class FollowUpAgent(Protocol):
    def analyze(self, case: AssistanceCase, now: datetime) -> dict: ...


class EscalationAgent(Protocol):
    def analyze(self, case: AssistanceCase, now: datetime, explicit: bool = False) -> dict: ...


class DoorstepCoordinatorAgent(Protocol):
    async def propose_assignment(self, request_id: str) -> str | None: ...
