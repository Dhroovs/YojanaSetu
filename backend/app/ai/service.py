import asyncio
import hashlib
import re
import secrets
from weakref import WeakValueDictionary

from fastapi import HTTPException
from langsmith import tracing_context

from app.agents.scheme_matcher import parse_profile
from app.ai.models import MatchResponse, Profile
from app.ai.providers import begin_model_usage, model_usage


class MatcherService:
    def __init__(self, store, matcher, settings):
        self.store, self.matcher, self.settings = store, matcher, settings
        self.slots = asyncio.Semaphore(2)
        self.conversation_locks = WeakValueDictionary()

    async def match(self, request, session_key: str):
        key = (session_key, request.conversation_id)
        lock = self.conversation_locks.setdefault(key, asyncio.Lock())
        async with asyncio.timeout(self.settings.ai_timeout_seconds):
            async with lock:
                return await self._match(request, session_key)

    async def _match(self, request, session_key: str):
        begin_model_usage()
        supplied_text = " ".join(
            [request.question, request.profile.state or "", request.profile.occupation or ""]
        )
        if re.search(r"\b\d[\d -]{10,}\d\b", supplied_text) or re.search(
            r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", supplied_text
        ):
            raise HTTPException(
                422, "Do not submit identity numbers, account details or contact information."
            )
        owner = hashlib.sha256(session_key.encode()).hexdigest()
        conversation_id = request.conversation_id or secrets.token_urlsafe(32)
        previous = None
        if request.conversation_id:
            previous = await self.store.conversation(conversation_id, owner)
            if previous is None:
                raise HTTPException(404, "Conversation not found or expired for this session.")
        profile = Profile(
            **{
                **(previous or {}).get("profile", {}),
                **parse_profile(request.question),
                **request.profile.model_dump(exclude_unset=True),
            }
        )
        async with self.slots:
            async with asyncio.timeout(self.settings.ai_timeout_seconds):
                # Never export citizen profile state to optional LangSmith tracing.
                with tracing_context(enabled=False):
                    result = await self.matcher.graph.ainvoke(
                        {
                            "question": request.question,
                            "scope": request.scope,
                            "profile": profile,
                            "previous_scheme_ids": (previous or {}).get("scheme_ids", []),
                            "trace": [],
                        }
                    )
        await self.store.save_conversation(
            conversation_id,
            owner,
            result["profile"],
            [r.scheme_id for r in result["recommendations"]][:10],
            self.settings.conversation_ttl_hours,
        )
        mode = (
            "llm-assisted extractive RAG"
            if self.matcher.model.enabled
            else "evidence-only RAG (no LLM)"
        )
        if any("unavailable" in warning for warning in result["warnings"]):
            mode = "evidence-only RAG (LLM unavailable)"
        return MatchResponse(
            conversation_id=conversation_id,
            profile=result["profile"],
            message=result["message"],
            recommendations=result["recommendations"],
            follow_up_questions=result["follow_up_questions"],
            warnings=result["warnings"],
            mode=mode,
            trace=result["trace"],
            model_usage=model_usage(),
        )
