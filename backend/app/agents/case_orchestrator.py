import re
import secrets
from datetime import timedelta
from typing import TypedDict

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context

from app.agents.case_agents import DocumentVerifier, EscalationAgent, FollowUpAgent
from app.cases.models import TERMINAL, Actor, AssistanceCase, AssistanceRequest, Stage, now_utc


class CaseGraphState(TypedDict, total=False):
    case_id: str
    actor: Actor
    body: AssistanceRequest
    key: str
    case: AssistanceCase
    intent: str
    result: dict
    trace: list[str]


class CaseOrchestrator:
    """Bounded case tasks. Model/document text can never select arbitrary tools or mutations."""

    def __init__(self, service, matcher_factory=None, matcher_session_key=None, seva_factory=None):
        self.service, self.matcher_factory = service, matcher_factory
        self.seva_factory = seva_factory
        self.matcher_session_key = matcher_session_key or secrets.token_urlsafe(32)
        graph = StateGraph(CaseGraphState)
        for name in (
            "identify_intent",
            "load_context",
            "documents",
            "followup",
            "escalation",
            "status",
            "scheme_match",
            "doorstep",
            "validate_result",
            "persist",
            "respond",
        ):
            graph.add_node(name, getattr(self, name))
        graph.add_edge(START, "identify_intent")
        graph.add_edge("identify_intent", "load_context")
        graph.add_conditional_edges(
            "load_context",
            lambda s: s["intent"],
            {
                name: name
                for name in (
                    "documents",
                    "followup",
                    "escalation",
                    "status",
                    "scheme_match",
                    "doorstep",
                )
            },
        )
        for name in ("documents", "followup", "escalation", "status", "scheme_match", "doorstep"):
            graph.add_edge(name, "validate_result")
        graph.add_edge("validate_result", "persist")
        graph.add_edge("persist", "respond")
        graph.add_edge("respond", END)
        self.graph = graph.compile()

    def step(self, state, name, **updates):
        return {**updates, "trace": state.get("trace", []) + [name]}

    async def identify_intent(self, state):
        body = state["body"]
        question = body.question.casefold()
        if re.search(r"\d[\d -]{9,}\d", question):
            raise HTTPException(422, "Do not include identity or account numbers.")
        intent = body.intent
        if intent == "auto":
            if any(word in question for word in ("doorstep", "sevasetu", "home visit")):
                intent = "doorstep"
            elif any(word in question for word in ("coordinator", "human", "escalat", "help from")):
                intent = "escalation"
            elif any(word in question for word in ("document", "checklist", "upload")):
                intent = "documents"
            elif any(word in question for word in ("follow", "remind", "appointment", "next")):
                intent = "followup"
            elif any(word in question for word in ("scheme", "eligible", "benefit")):
                intent = "scheme_match"
            else:
                intent = "status"
        return self.step(state, "identify_intent", intent=intent)

    async def load_context(self, state):
        case = await self.service.authorized(state["case_id"], state["actor"])
        return self.step(state, "load_authorized_context", case=case)

    async def documents(self, state):
        return self.step(
            state, "document_verifier", result=DocumentVerifier().analyze(state["case"], now_utc())
        )

    async def followup(self, state):
        return self.step(
            state, "follow_up", result=FollowUpAgent().analyze(state["case"], now_utc())
        )

    async def escalation(self, state):
        return self.step(
            state,
            "escalation",
            result=EscalationAgent(self.service.settings).analyze(
                state["case"], now_utc(), explicit=True
            ),
        )

    async def status(self, state):
        case = state["case"]
        return self.step(
            state,
            "case_status",
            result={
                "agent": "case_status",
                "stage": case.stage,
                "status": case.status,
                "next_action": DocumentVerifier().analyze(case, now_utc())["next_action"],
                "official_status": "Unknown. Internal stages do not indicate government approval.",
            },
        )

    async def scheme_match(self, state):
        if self.matcher_factory is None:
            raise HTTPException(503, "Scheme Matcher is not configured for this case workflow.")
        from app.ai.models import MatchRequest

        matcher = await self.matcher_factory()
        response = await matcher.match(
            MatchRequest(
                question=(
                    f"{state['body'].question} Current case scheme: {state['case'].scheme_id}."
                ),
                conversation_id=state["body"].scheme_conversation_id,
            ),
            self.matcher_session_key,
        )
        return self.step(
            state,
            "scheme_matcher",
            result={
                "agent": "scheme_matcher",
                "match": response.model_dump(mode="json"),
                "next_action": "Review the cited source evidence.",
            },
        )

    async def doorstep(self, state):
        booking_id = state["body"].doorstep_request_id
        result = {
            "agent": "doorstep_coordinator",
            "next_action": (
                "Create a consented SevaSetu request linked to this case. No booking was created."
            ),
        }
        if booking_id:
            if self.seva_factory is None:
                raise HTTPException(503, "Doorstep coordination is not configured.")
            from app.agents.doorstep_coordinator import DoorstepCoordinator

            service = await self.seva_factory()
            booking = await service.authorized(booking_id, state["actor"])
            if (
                booking["case_id"] != state["case_id"]
                or booking["owner_id"] != state["case"].owner_id
            ):
                raise HTTPException(404, "No linked doorstep request found.")
            result.update(await DoorstepCoordinator(service).run(booking_id, state["actor"]))
        return self.step(state, "doorstep_coordinator", result=result)

    async def validate_result(self, state):
        if not isinstance(state["result"], dict) or "agent" not in state["result"]:
            raise HTTPException(500, "Case workflow returned an invalid result.")
        return self.step(state, "validate_result")

    async def persist(self, state):
        body, actor = state["body"], state["actor"]
        if not body.apply_changes:
            return self.step(state, "read_only_no_case_mutation")
        if state["intent"] in {"status", "scheme_match", "doorstep"}:
            raise HTTPException(422, "This intent is read-only; disable apply_changes.")

        async def change(case):
            if case.stage in TERMINAL:
                raise HTTPException(409, "Reopen the assistance task before changing it.")
            if state["intent"] == "escalation":
                self.service.escalate(case, actor, "human_assistance_requested")
            elif state["intent"] == "followup":
                if not any(
                    f.reason == "manual" and f.status == "scheduled" for f in case.followups
                ):
                    self.service.schedule(
                        case,
                        actor,
                        "manual",
                        now_utc() + timedelta(hours=self.service.settings.follow_up_interval_hours),
                        body.note,
                    )
            elif state["intent"] == "documents":
                if (
                    DocumentVerifier().analyze(case, now_utc())["ready_for_human_review"]
                    and case.stage == Stage.documents_pending
                ):
                    self.service.stage(case, Stage.ready_for_human_review)
            case.last_workflow = {
                "intent": state["intent"],
                "actor_id": actor.id,
                "at": now_utc(),
                "trace": state["trace"],
            }
            self.service.event(case, actor, "case_agent_action", state["intent"])

        case = await self.service.mutate(
            state["case_id"],
            actor,
            body.revision,
            state["key"],
            "agent_" + state["intent"],
            body.model_dump(exclude={"revision"}),
            change,
        )
        return self.step(state, "persist_permitted_changes", case=case)

    async def respond(self, state):
        return self.step(state, "respond")

    async def run(self, case_id, actor, body, key):
        with tracing_context(enabled=False):
            state = await self.graph.ainvoke(
                {"case_id": case_id, "actor": actor, "body": body, "key": key, "trace": []}
            )
        return {
            "case_id": case_id,
            "revision": state["case"].revision,
            "result": state["result"],
            "trace": state["trace"],
            "applied": body.apply_changes,
            "disclaimer": "Internal assistance only. No official approval or KYC.",
        }
