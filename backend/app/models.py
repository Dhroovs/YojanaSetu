from datetime import date, datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    citizen = "citizen"
    worker = "worker"
    coordinator = "coordinator"
    admin = "admin"


class CaseStatus(str, Enum):
    received = "received"
    under_review = "under_review"
    awaiting_information = "awaiting_information"
    resolved = "resolved"
    escalated = "escalated"
    on_hold = "on_hold"
    closed = "closed"


class GovernmentScheme(BaseModel):
    id: str
    title: str
    category: str
    summary: str
    eligibility: list[str]
    documents: list[str]
    guidance: list[str]
    is_demo: bool = True
    source_url: str | None = None
    department: str | None = None
    scope: str | None = None
    geographic_coverage: list[str] | None = None
    beneficiary_categories: list[str] | None = None
    age_restrictions: str | None = None
    income_restrictions: str | None = None
    occupation_requirements: str | None = None
    gender_requirements: str | None = None
    disability_conditions: str | None = None
    benefits: list[str] | None = None
    application_url: str | None = None
    source_references: list[str] = Field(default_factory=list)
    last_verified_at: date | None = None
    information_completeness: str = "partial"


class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    scheme_id: str = Field(min_length=1, max_length=80)
    assistance_type: str = Field(min_length=3, max_length=120)


class CitizenCase(CaseCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: CaseStatus = CaseStatus.received
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DoorstepCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    district: str = Field(min_length=2, max_length=80)
    service_type: str = Field(min_length=3, max_length=120)
    preferred_date: date


class DoorstepRequest(DoorstepCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: CaseStatus = CaseStatus.received
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
