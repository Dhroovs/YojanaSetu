from datetime import date, datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Profile(StrictModel):
    state: str | None = Field(default=None, max_length=60)
    age: int | None = Field(default=None, ge=0, le=120)
    household_income: int | None = Field(default=None, ge=0, le=1_000_000_000)
    occupation: str | None = Field(default=None, max_length=80)
    student: bool | None = None
    employed: bool | None = None
    farming: bool | None = None
    disability: bool | None = None
    gender: Literal["female", "male", "other"] | None = None
    landholding_family: bool | None = None
    institutional_landholder: bool | None = None
    family_income_taxpayer: bool | None = None


class Citation(StrictModel):
    chunk_id: str
    source_id: str
    document_title: str
    official_url: HttpUrl
    page: int | None = None
    quote: str
    content_hash: str
    verification_status: Literal["verified", "synthetic"]
    retrieved_at: datetime
    published_at: date | None = None


class Rule(StrictModel):
    field: Literal[
        "state",
        "age",
        "household_income",
        "occupation",
        "student",
        "employed",
        "farming",
        "disability",
        "gender",
        "landholding_family",
        "institutional_landholder",
        "family_income_taxpayer",
    ]
    operator: Literal["eq", "gte", "lte", "in"]
    value: str | int | bool | list[str]
    source_id: str
    quote: str = Field(min_length=12, max_length=1500)

    @model_validator(mode="after")
    def valid_threshold(self):
        numeric = self.field in {"age", "household_income"}
        boolean = self.field in {
            "student",
            "employed",
            "farming",
            "disability",
            "landholding_family",
            "institutional_landholder",
            "family_income_taxpayer",
        }
        if numeric and (type(self.value) is not int or self.operator not in {"eq", "gte", "lte"}):
            raise ValueError("Numeric rules require integer thresholds")
        if boolean and (type(self.value) is not bool or self.operator != "eq"):
            raise ValueError("Boolean rules require eq and a boolean")
        if not numeric and not boolean:
            if self.operator == "in" and not isinstance(self.value, list):
                raise ValueError("in requires a list")
            if self.operator != "in" and (self.operator != "eq" or type(self.value) is not str):
                raise ValueError("Text rules require eq/string or in/list")
        return self


class SourceManifest(StrictModel):
    source_id: str = Field(pattern=r"^[a-z0-9-]{3,80}$")
    scheme_id: str = Field(pattern=r"^[a-z0-9-]{3,80}$")
    scheme_name: str = Field(min_length=3, max_length=200)
    department: str
    scope: Literal["central", "state"]
    geographic_coverage: list[str] = Field(default_factory=list)
    category: str
    official_url: HttpUrl
    document_title: str
    published_at: date | None = None
    reviewed_at: date
    verification_status: Literal["verified", "synthetic"]
    completeness: Literal["partial", "complete"] = "partial"
    beneficiary_categories: list[str] | None = None
    age_restrictions: str | None = None
    income_restrictions: str | None = None
    occupation_requirements: str | None = None
    gender_requirements: str | None = None
    disability_conditions: str | None = None
    required_documents: list[str] | None = None
    benefits: list[str] | None = None
    application_process: list[str] | None = None
    application_url: HttpUrl | None = None
    rules: list[Rule] = Field(default_factory=list)
    field_evidence: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def review_date(self):
        if self.reviewed_at > datetime.now(timezone.utc).date():
            raise ValueError("Review date cannot be in the future")
        if self.verification_status == "synthetic" and self.completeness == "complete":
            # Synthetic fixtures may be rule-complete, but cannot be promoted to official data.
            pass
        if any(rule.source_id != self.source_id for rule in self.rules):
            raise ValueError("Rules in a manifest must cite that source")
        return self


class SourceRecord(SourceManifest):
    retrieved_at: datetime
    content_hash: str
    index_version: str
    chunk_count: int


class Chunk(StrictModel):
    id: str
    text: str
    source_id: str
    scheme_id: str
    document_title: str
    official_url: str
    page: int | None
    content_hash: str
    index_version: str
    verification_status: str
    scope: str


class EligibilityStatus(str, Enum):
    potential = "Potentially eligible"
    missing = "Possibly eligible — more information required"
    excluded = "Not eligible based on a documented condition"
    unknown = "Unable to determine"


class ConditionResult(StrictModel):
    field: str
    outcome: Literal["met", "not_met", "unknown"]
    explanation: str
    citation: Citation


class Recommendation(StrictModel):
    scheme_id: str
    scheme_name: str
    status: EligibilityStatus
    conditions: list[ConditionResult]
    evidence: list[Citation]
    warnings: list[str]
    completeness: str


class MatchRequest(StrictModel):
    question: str = Field(min_length=3, max_length=1500)
    profile: Profile = Field(default_factory=Profile)
    scope: Literal["central", "state"] | None = None
    conversation_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{40,100}$")


class MatchResponse(StrictModel):
    conversation_id: str
    profile: Profile
    message: str
    recommendations: list[Recommendation]
    follow_up_questions: list[str]
    warnings: list[str]
    mode: str
    trace: list[str]
    disclaimer: str = "Preliminary guidance only. No official approval or application submission."
