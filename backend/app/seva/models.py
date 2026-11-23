from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from app.cases.models import Change, Preferences, Strict, new_id, now_utc


class Slot(Strict):
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("Appointment times require a timezone offset")
        # Stable precision across JSON and MongoDB's millisecond datetime representation.
        return value.astimezone(timezone.utc).replace(microsecond=0)

    @model_validator(mode="after")
    def ordered(self):
        minutes = (self.end - self.start).total_seconds() / 60
        if not 15 <= minutes <= 240:
            raise ValueError("A service window must be 15–240 minutes")
        return self


class Location(Strict):
    district: str = Field(min_length=2, max_length=80)
    mandal: str = Field(min_length=2, max_length=80)
    village: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=5, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    map_consent: bool = False

    @model_validator(mode="after")
    def location_consent(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both coordinates or neither")
        if self.latitude is not None and not self.map_consent:
            raise ValueError("Explicit map-location consent is required")
        return self


Category = Literal[
    "scheme_guidance", "document_assistance", "digital_assistance", "accessibility_support"
]
Language = Literal["en", "hi", "te"]
ShortText = Annotated[str, Field(min_length=1, max_length=200)]


class BookingInput(Strict):
    category: Category
    scheme_id: str | None = Field(default=None, max_length=80)
    case_id: str | None = Field(default=None, max_length=80)
    description: str = Field(min_length=5, max_length=600)
    preferred_window: Slot
    location: Location
    contact_preference: Literal["in_app"] = "in_app"
    accessibility: list[
        Literal["wheelchair_access", "hearing_support", "reading_help", "caregiver_support"]
    ] = Field(default_factory=list, max_length=4)
    language: Language = "en"
    caregiver_present: bool | None = None
    share_with_assigned_worker: bool
    preferences: Preferences = Field(default_factory=Preferences)

    @field_validator("description")
    @classmethod
    def no_secrets(cls, value):
        import re

        if re.search(r"\d[\d -]{9,}\d|\b(?:otp|password|pin)\s*[:=]?\s*\d+", value, re.I):
            raise ValueError("Do not enter identity numbers, credentials or OTPs")
        return value


class VisitStage(str, Enum):
    requested = "requested"
    pending = "pending_coordinator_review"
    approved = "approved_for_assignment"
    assigned = "worker_assigned"
    scheduled = "visit_scheduled"
    en_route = "worker_en_route"
    in_progress = "visit_in_progress"
    completion_review = "completion_pending_review"
    completed = "visit_completed"
    followup = "follow_up_required"
    closed = "closed"
    rejected = "rejected"
    cancelled = "cancelled"
    reschedule = "rescheduling_requested"
    unavailable = "no_worker_available"
    no_show = "no_show"
    escalated = "escalated"


TERMINAL = {VisitStage.closed, VisitStage.cancelled, VisitStage.rejected}


class WorkerInput(Strict):
    display_name: str = Field(min_length=2, max_length=80)
    organization_id: str | None = Field(default=None, max_length=80)
    kind: Literal["ngo_volunteer", "field_worker", "service_partner", "coordinator"]
    categories: list[Category] = Field(min_length=1, max_length=4)
    languages: list[Language] = Field(min_length=1, max_length=3)
    districts: list[ShortText] = Field(min_length=1, max_length=30)
    areas: list[ShortText] = Field(default_factory=list, max_length=50)
    capabilities: list[ShortText] = Field(default_factory=list, max_length=10)
    qualifications: list[ShortText] = Field(default_factory=list, max_length=10)
    capacity: int = Field(default=5, ge=1, le=20)


class Availability(Change):
    slots: list[Slot] = Field(max_length=200)

    @model_validator(mode="after")
    def no_overlap(self):
        ordered = sorted(self.slots, key=lambda s: s.start)
        if any(a.end > b.start for a, b in zip(ordered, ordered[1:])):
            raise ValueError("Availability windows cannot overlap")
        return self


class WorkerUpdate(Change):
    profile: WorkerInput
    active: bool = True
    confirmed: bool


class BookingPreferences(Change):
    preferences: Preferences
    language: Language
    share_with_assigned_worker: bool
    confirmed: bool


class WorkerVerification(Change):
    status: Literal[
        "pending_verification",
        "verified_internally",
        "authorization_confirmed",
        "suspended",
        "expired",
    ]
    expires_at: datetime | None = None
    evidence_url: str | None = Field(default=None, max_length=400)
    confirmed: bool


class OrganizationInput(Strict):
    display_name: str = Field(min_length=2, max_length=100)
    kind: Literal["ngo", "service_partner", "field_team"]
    active: bool = True
    verified_internally: bool = False
    confirmed: bool = False


class BookingAction(Change):
    action: Literal[
        "claim",
        "approve",
        "reject",
        "cancel",
        "accept",
        "decline",
        "en_route",
        "check_in",
        "submit_outcome",
        "confirm_completion",
        "citizen_confirm",
        "reschedule",
        "report_problem",
        "no_show",
        "request_followup",
        "close",
        "feedback",
        "resolve_escalation",
        "no_worker_available",
    ]
    confirmed: bool = False
    window: Slot | None = None
    services_performed: list[Category] = Field(default_factory=list, max_length=4)
    documents_assisted: list[ShortText] = Field(default_factory=list, max_length=10)
    task_checklist: list[ShortText] = Field(default_factory=list, max_length=20)
    followup_at: datetime | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


class Assignment(Change):
    worker_id: str
    window: Slot
    confirmed: bool
    override_reason: str = Field(default="", max_length=400)


def fresh_booking(body, owner, key, digest):
    return {
        **body.model_dump(mode="python"),
        "id": new_id(),
        "owner_id": owner,
        "stage": VisitStage.pending.value,
        "created_at": now_utc(),
        "updated_at": now_utc(),
        "revision": 0,
        "coordinator_id": None,
        "approval": None,
        "worker_id": None,
        "appointment": None,
        "assignment_accepted": False,
        "outcome": None,
        "citizen_confirmed": False,
        "feedback": None,
        "audit": [],
        "operations": [],
        "notifications": [],
        "escalations": [],
        "next_automation_at": now_utc(),
        "case_sync_pending": False,
        "creation_key": key,
        "creation_fingerprint": digest,
        "disclaimer": "An internal assistance visit is not government scheme approval or KYC.",
    }
