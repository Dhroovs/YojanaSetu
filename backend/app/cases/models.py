from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import CaseStatus, CitizenCase, UserRole


def now_utc():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid4())


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Actor(Strict):
    id: str
    username: str
    role: UserRole


class Login(Strict):
    username: str = Field(pattern=r"^[a-zA-Z0-9_-]{3,50}$")
    password: str = Field(min_length=12, max_length=128)


class Stage(str, Enum):
    draft = "draft"
    documents_pending = "documents_pending"
    ready_for_human_review = "ready_for_human_review"
    assistance_in_progress = "assistance_in_progress"
    waiting_for_external_update = "waiting_for_external_update"
    completed = "completed"
    on_hold = "on_hold"
    escalated = "escalated"
    closed = "closed"


TERMINAL = {Stage.completed, Stage.closed}


class ReviewStatus(str, Enum):
    received = "received"
    readable = "technically_readable"
    unreadable = "unreadable"
    missing = "missing"
    human = "needs_human_review"
    accepted = "accepted_for_assistance_checklist"


class ChecklistItem(Strict):
    id: str
    label: str
    source_ids: list[str]
    is_demo: bool = False


class Document(Strict):
    id: str = Field(default_factory=new_id)
    item_id: str
    storage_key: str = Field(exclude=True)
    content_hash: str
    media_type: str
    byte_count: int
    uploaded_by: str
    created_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime
    technical_status: ReviewStatus
    review_status: ReviewStatus = ReviewStatus.human
    technical_notes: list[str]
    reviewed_by: str | None = None
    review_note: str | None = None
    reviewed_at: datetime | None = None
    deleted_at: datetime | None = None
    storage_removed: bool = False


class FollowUp(Strict):
    id: str = Field(default_factory=new_id)
    reason: Literal[
        "missing_documents", "coordinator_review", "appointment", "manual", "inactivity"
    ]
    due_at: datetime
    status: Literal["scheduled", "delivered", "cancelled"] = "scheduled"
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)
    note: str = ""


class Reminder(Strict):
    id: str
    follow_up_id: str
    reason: str
    created_at: datetime
    message: str = (
        "An internal assistance follow-up needs your attention. Open the case for details."
    )
    acknowledged_by: list[str] = Field(default_factory=list)


class Escalation(Strict):
    id: str = Field(default_factory=new_id)
    reason: str
    severity: Literal["normal", "high"]
    status: Literal["open", "acknowledged", "resolved"] = "open"
    owner_coordinator_id: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)
    acknowledged_by: str | None = None
    resolution_note: str | None = None
    resolved_at: datetime | None = None
    reopened_count: int = 0


class Event(Strict):
    id: str = Field(default_factory=new_id)
    action: str
    actor_id: str
    at: datetime = Field(default_factory=now_utc)
    note: str = ""


class Preferences(Strict):
    in_app: bool = True
    quiet_start: int = Field(default=21, ge=0, le=23)
    quiet_end: int = Field(default=8, ge=0, le=23)


class AssistanceCase(CitizenCase):
    owner_id: str
    stage: Stage = Stage.draft
    resume_stage: Stage | None = None
    scheme_source_versions: dict[str, str] = Field(default_factory=dict)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    checklist_verified: bool = False
    is_demo: bool = False
    documents: list[Document] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    followups: list[FollowUp] = Field(default_factory=list)
    reminders: list[Reminder] = Field(default_factory=list)
    escalations: list[Escalation] = Field(default_factory=list)
    coordinator_id: str | None = None
    worker_ids: list[str] = Field(default_factory=list)
    activity: list[Event] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
    updated_at: datetime = Field(default_factory=now_utc)
    last_human_activity_at: datetime = Field(default_factory=now_utc)
    next_automation_at: datetime = Field(default_factory=now_utc)
    closed_at: datetime | None = None
    revision: int = 0
    operations: list[dict] = Field(default_factory=list, exclude=True)
    creation_key: str = Field(exclude=True)
    creation_fingerprint: str = Field(exclude=True)
    last_workflow: dict | None = None
    retention_purging: bool = False
    disclaimer: str = (
        "Internal assistance only. No official approval, legal identity verification or KYC."
    )


class Change(Strict):
    revision: int = Field(ge=0)
    note: str = Field(default="", max_length=600)

    @field_validator("note")
    @classmethod
    def no_identity_numbers(cls, value):
        import re

        if re.search(r"\d[\d -]{9,}\d", value):
            raise ValueError("Do not include identity/account/contact numbers")
        return value


class StageChange(Change):
    stage: Stage
    confirmed: bool = False
    reported_external_update: bool = False


class Assignment(Change):
    coordinator_id: str
    worker_ids: list[str] = Field(default_factory=list, max_length=10)
    confirmed: bool = False


class DocumentReview(Change):
    status: Literal["accepted_for_assistance_checklist", "needs_human_review", "unreadable"]


class FollowUpCreate(Change):
    reason: Literal[
        "missing_documents", "coordinator_review", "appointment", "manual", "inactivity"
    ]
    due_at: datetime

    @field_validator("due_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None:
            raise ValueError("Include a timezone offset")
        return value


class EscalationChange(Change):
    action: Literal["acknowledge", "resolve", "reopen"]


class AssistanceRequest(Change):
    question: str = Field(min_length=3, max_length=500)
    intent: Literal[
        "auto", "documents", "followup", "escalation", "status", "scheme_match", "doorstep"
    ] = "auto"
    apply_changes: bool = False
    doorstep_request_id: str | None = Field(default=None, max_length=80)
    scheme_conversation_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{40,100}$")


STAGE_STATUS = {
    Stage.draft: CaseStatus.received,
    Stage.documents_pending: CaseStatus.awaiting_information,
    Stage.ready_for_human_review: CaseStatus.under_review,
    Stage.assistance_in_progress: CaseStatus.under_review,
    Stage.waiting_for_external_update: CaseStatus.under_review,
    Stage.completed: CaseStatus.resolved,
    Stage.on_hold: CaseStatus.on_hold,
    Stage.escalated: CaseStatus.escalated,
    Stage.closed: CaseStatus.closed,
}
