from typing import TypedDict

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context

from app.cases.models import Actor
from app.seva.models import Assignment, Slot


class DoorstepState(TypedDict, total=False):
    actor: Actor
    booking_id: str
    booking: dict
    candidates: list[dict]
    missing: list[str]
    trace: list[str]
    result: dict
    assignment: Assignment | None
    key: str


class DoorstepCoordinator:
    """Bounded proposals; optional assignment must carry explicit human confirmation."""

    def __init__(self, service):
        self.service = service
        graph = StateGraph(DoorstepState)
        nodes = [
            self.load_authorized_context,
            self.identify_missing_information,
            self.check_eligible_workers_and_availability,
            self.rank_candidates,
            self.propose_appointment,
            self.confirm_human_action,
            self.evaluate_escalation,
            self.generate_grounded_response,
        ]
        previous = START
        for node in nodes:
            graph.add_node(node.__name__, node)
            graph.add_edge(previous, node.__name__)
            previous = node.__name__
        graph.add_edge(previous, END)
        self.graph = graph.compile()

    def step(self, state, name, **updates):
        return {**updates, "trace": state.get("trace", []) + [name]}

    async def load_authorized_context(self, s):
        booking = await self.service.authorized(s["booking_id"], s["actor"])
        if booking["case_id"]:
            case = await self.service.cases.store.load(booking["case_id"])
            if not case or case.owner_id != booking["owner_id"]:
                raise HTTPException(409, "Linked case ownership no longer matches.")
        return self.step(s, "load_authorized_context", booking=booking)

    async def identify_missing_information(self, s):
        missing = (
            []
            if s["booking"]["share_with_assigned_worker"]
            else ["Explicit consent to share necessary details with an assigned worker"]
        )
        return self.step(s, "identify_missing_information", missing=missing)

    async def check_eligible_workers_and_availability(self, s):
        window = (
            s["assignment"].window
            if s.get("assignment")
            else Slot.model_validate(s["booking"]["preferred_window"])
        )
        candidates = await self.service.candidates(s["booking"], window)
        return self.step(s, "check_eligible_workers_and_availability", candidates=candidates)

    async def rank_candidates(self, s):
        return self.step(
            s,
            "rank_candidates",
            candidates=sorted(s["candidates"], key=lambda c: (c["workload"], c["worker_id"])),
        )

    async def propose_appointment(self, s):
        return self.step(
            s,
            "propose_appointment",
            result={
                "applied": False,
                "human_approval_required": True,
                "missing_information": s["missing"],
            },
        )

    async def confirm_human_action(self, s):
        if not s.get("assignment"):
            return self.step(s, "read_only_no_booking_change")
        result = await self.service.assign(s["booking_id"], s["actor"], s["assignment"], s["key"])
        return self.step(
            s,
            "confirm_authorized_assignment_and_schedule_notifications",
            result={**s["result"], "applied": True, "booking": result},
        )

    async def evaluate_escalation(self, s):
        reasons = [e["reason"] for e in s["booking"]["escalations"] if e["status"] == "open"]
        if not s["candidates"]:
            reasons.append(
                "No eligible worker in this window; request human review or rescheduling."
            )
        return self.step(
            s, "evaluate_escalation", result={**s["result"], "escalation_recommendations": reasons}
        )

    async def generate_grounded_response(self, s):
        from app.ai.providers import LanguageModel

        staff = s["actor"].role in {"admin", "coordinator"}
        summary = await LanguageModel(self.service.settings).grounded_summary(
            [
                f"Internal visit stage: {s['booking']['stage']}.",
                f"Requested service category: {s['booking']['category']}.",
                "A confirmed visit requires coordinator approval and worker acceptance.",
                "A SevaSetu visit does not grant government approval or certification.",
            ]
        )
        return self.step(
            s,
            "generate_grounded_response",
            result={
                **s["result"],
                "booking_id": s["booking_id"],
                "category": s["booking"]["category"],
                "candidates": s["candidates"] if staff else [],
                "next_action": "Coordinator approval and worker acceptance are required.",
                "grounded_summary": summary,
                "disclaimer": "Internal assistance, not government approval or certification.",
            },
        )

    async def run(self, booking_id, actor, assignment=None, key=""):
        with tracing_context(enabled=False):
            result = await self.graph.ainvoke(
                {
                    "booking_id": booking_id,
                    "actor": actor,
                    "assignment": assignment,
                    "key": key,
                    "trace": [],
                }
            )
        return {**result["result"], "trace": result["trace"]}
