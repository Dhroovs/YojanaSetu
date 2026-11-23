import asyncio
import io
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pymupdf
import pytest
from fastapi import HTTPException
from PIL import Image

from app.agents.case_agents import DocumentVerifier, EscalationAgent, FollowUpAgent
from app.agents.case_orchestrator import CaseOrchestrator
from app.auth import hash_password, verify_password
from app.cases.models import (
    Actor,
    AssistanceCase,
    AssistanceRequest,
    ChecklistItem,
    DocumentReview,
    EscalationChange,
    FollowUp,
    Reminder,
    Stage,
    StageChange,
    now_utc,
)
from app.cases.service import CaseService
from app.cases.storage import LocalPrivateStorage, inspect_document
from app.cases.store import stored_case
from app.config import Settings


def run(value):
    return asyncio.run(value)


def synthetic_pdf(text=True):
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        if text:
            page.insert_text((60, 60), "SYNTHETIC TEST DOCUMENT - no identity numbers")
        return pdf.tobytes()


def synthetic_image(size=(640, 640)):
    output = io.BytesIO()
    Image.new("RGB", size, "white").save(output, format="PNG")
    return output.getvalue()


def case_record():
    return AssistanceCase(
        owner_id="citizen-a",
        scheme_id="synthetic",
        assistance_type="Test help",
        creation_key="test-key",
        creation_fingerprint="test-fingerprint",
        stage=Stage.documents_pending,
        checklist_verified=True,
        checklist=[
            ChecklistItem(
                id="household", label="Synthetic household record", source_ids=["test-source"]
            )
        ],
    )


class MemoryCaseStore:
    def __init__(self, case):
        self.case = case.model_copy(deep=True)

    async def load(self, case_id):
        return self.case.model_copy(deep=True) if self.case.id == case_id else None

    async def save(self, case, revision):
        if self.case.revision != revision:
            raise HTTPException(409, "Conflict")
        self.case = case.model_copy(deep=True)

    async def due_cases(self, now, limit):
        return [self.case.model_copy(deep=True)] if self.case.next_automation_at <= now else []


@pytest.fixture
def service(tmp_path):
    return CaseService(
        MemoryCaseStore(case_record()),
        SimpleNamespace(),
        LocalPrivateStorage(tmp_path / "private"),
        Settings(_env_file=None),
    )


def actor(role="citizen", user_id="citizen-a"):
    return Actor(id=user_id, username="synthetic-user", role=role)


def test_password_hashes_are_salted_and_verified():
    first, second = hash_password("synthetic-password"), hash_password("synthetic-password")
    assert first != second
    assert "synthetic-password" not in first
    assert verify_password("synthetic-password", first)
    assert not verify_password("incorrect-password", first)
    assert not verify_password("password", "broken")


@pytest.mark.parametrize(
    "who",
    [actor(user_id="citizen-b"), actor("worker", "worker"), actor("coordinator", "coordinator")],
)
def test_unrelated_users_cannot_access_case(service, who):
    with pytest.raises(HTTPException) as exc:
        run(service.authorized(service.store.case.id, who))
    assert exc.value.status_code == 404


def test_assigned_staff_and_admin_access(service):
    service.store.case.coordinator_id = "coord"
    service.store.case.worker_ids = ["worker"]
    for who in (
        actor(),
        actor("coordinator", "coord"),
        actor("worker", "worker"),
        actor("admin", "admin"),
    ):
        assert run(service.authorized(service.store.case.id, who))


def test_private_storage_keys_and_access_paths(service):
    key = service.storage.put(b"synthetic", "pdf")
    assert service.storage.path(key).read_bytes() == b"synthetic"
    for bad in ("../secret.pdf", "/etc/passwd", "citizen.pdf", "C:\\secret.pdf"):
        with pytest.raises(ValueError):
            service.storage.path(bad)
    service.storage.delete(key)
    assert not service.storage.path(key).exists()


@pytest.mark.parametrize(
    "payload,mime",
    [
        (b"notpdf", "application/pdf"),
        (b"executable", "application/x-msdownload"),
        (b"badimage", "image/png"),
        (synthetic_image(), "image/jpeg"),
        (b"", "application/pdf"),
    ],
)
def test_upload_validation(service, payload, mime):
    with pytest.raises(HTTPException):
        inspect_document(payload, mime, service.settings)


def test_pdf_and_image_technical_assistance(service):
    data, extension, digest, status, notes = inspect_document(
        synthetic_pdf(), "application/pdf", service.settings
    )
    assert extension == "pdf" and status == "technically_readable" and digest and notes
    assert data.startswith(b"%PDF-")
    assert (
        inspect_document(synthetic_pdf(False), "application/pdf", service.settings)[3]
        == "needs_human_review"
    )
    assert (
        inspect_document(synthetic_image((100, 100)), "image/png", service.settings)[3]
        == "needs_human_review"
    )


def test_duplicate_upload_review_and_serialization(service):
    case = service.store.case
    payload = synthetic_pdf()
    first = run(
        service.upload(
            case.id, actor(), 0, "household", payload, "application/pdf", "upload-key-123456789"
        )
    )
    second = run(
        service.upload(
            case.id,
            actor(),
            first.revision,
            "household",
            payload,
            "application/pdf",
            "other-key-123456789",
        )
    )
    assert len(second.documents) == 1
    assert second.documents[0].review_status == "needs_human_review"
    assert "storage_key" not in second.model_dump()["documents"][0]
    assert "storage_key" in stored_case(second)["documents"][0]
    assert not DocumentVerifier().analyze(second, now_utc())["ready_for_human_review"]
    with pytest.raises(HTTPException):
        run(
            service.review(
                case.id,
                second.documents[0].id,
                actor(),
                DocumentReview(
                    revision=second.revision,
                    status="accepted_for_assistance_checklist",
                    note="Synthetic review",
                ),
                "review-key-123456789",
            )
        )
    service.store.case.coordinator_id = "coord"
    reviewed = run(
        service.review(
            case.id,
            second.documents[0].id,
            actor("coordinator", "coord"),
            DocumentReview(
                revision=second.revision,
                status="accepted_for_assistance_checklist",
                note="Synthetic checklist only",
            ),
            "review-key-123456789",
        )
    )
    assert reviewed.stage == Stage.ready_for_human_review
    assert DocumentVerifier().analyze(reviewed, now_utc())["ready_for_human_review"]


def test_idempotency_and_stale_version_conflicts(service):
    case = service.store.case

    async def change(c):
        service.event(c, actor(), "test")

    first = run(service.mutate(case.id, actor(), 0, "mutation-key-123456789", "test", {}, change))
    repeated = run(
        service.mutate(case.id, actor(), 0, "mutation-key-123456789", "test", {}, change)
    )
    assert len(repeated.activity) == len(first.activity) == 1
    with pytest.raises(HTTPException) as exc:
        run(service.mutate(case.id, actor(), 0, "different-key-123456789", "test", {}, change))
    assert exc.value.status_code == 409
    with pytest.raises(HTTPException):
        run(
            service.mutate(
                case.id, actor(), 1, "mutation-key-123456789", "test", {"different": True}, change
            )
        )


def test_sensitive_stage_changes_require_role_and_confirmation(service):
    case = service.store.case
    for who in (actor(), actor("worker", "worker")):
        with pytest.raises(HTTPException) as exc:
            run(
                service.transition(
                    case.id,
                    who,
                    StageChange(
                        revision=0, stage="closed", confirmed=True, note="Synthetic closure"
                    ),
                    "close-key-123456789",
                )
            )
        assert exc.value.status_code == 403
    with pytest.raises(HTTPException):
        run(
            service.transition(
                case.id,
                actor("admin", "admin"),
                StageChange(revision=0, stage="closed"),
                "close-key-123456789",
            )
        )
    closed = run(
        service.transition(
            case.id,
            actor("admin", "admin"),
            StageChange(revision=0, stage="closed", confirmed=True, note="Synthetic closure"),
            "close-key-123456789",
        )
    )
    assert closed.stage == Stage.closed
    reopened = run(
        service.transition(
            case.id,
            actor("admin", "admin"),
            StageChange(
                revision=closed.revision,
                stage="documents_pending",
                confirmed=True,
                note="Synthetic reopening",
            ),
            "reopen-key-123456789",
        )
    )
    assert reopened.stage == Stage.documents_pending


def test_unknown_checklist_never_becomes_ready(service):
    case = service.store.case
    case.checklist, case.checklist_verified = [], False
    assert not DocumentVerifier().analyze(case, now_utc())["ready_for_human_review"]


def test_escalation_rules_dedup_resolution_and_reopen(service):
    case = service.store.case
    service.escalate(case, actor(), "human_assistance_requested")
    service.escalate(case, actor(), "human_assistance_requested")
    assert len(case.escalations) == 1 and case.stage == Stage.escalated
    case.coordinator_id = "coord"
    escalation = case.escalations[0]
    resolved = run(
        service.escalation_action(
            case.id,
            escalation.id,
            actor("coordinator", "coord"),
            EscalationChange(
                revision=0, action="resolve", note="Synthetic human assistance recorded"
            ),
            "resolve-key-123456789",
        )
    )
    assert resolved.stage == Stage.documents_pending
    reopened = run(
        service.escalation_action(
            case.id,
            escalation.id,
            actor("coordinator", "coord"),
            EscalationChange(revision=resolved.revision, action="reopen", note="Still unresolved"),
            "reopen-key-123456789",
        )
    )
    assert reopened.escalations[0].reopened_count == 1
    assert reopened.stage == Stage.escalated


def test_deterministic_escalation_triggers(service):
    case = service.store.case
    now = now_utc()
    case.last_human_activity_at = now - timedelta(days=10)
    case.reminders = [
        Reminder(
            id=str(i),
            follow_up_id=str(i),
            reason="missing_documents",
            created_at=now - timedelta(days=i + 1),
        )
        for i in range(3)
    ]
    case.missing_information.append("conflicting_information")
    reasons = {
        t["reason"] for t in EscalationAgent(service.settings).analyze(case, now)["triggers"]
    }
    assert {"case_inactivity", "repeated_missing_documents", "conflicting_information"} <= reasons


def test_quiet_hours_and_frequency(service):
    case = service.store.case
    # 22:00 IST -> 08:00 IST next day.
    now = datetime(2026, 11, 17, 16, 30, tzinfo=timezone.utc)
    allowed = FollowUpAgent().next_allowed(case, now, 24)
    assert allowed == datetime(2026, 11, 18, 2, 30, tzinfo=timezone.utc)
    case.reminders = [Reminder(id="test", follow_up_id="test", reason="manual", created_at=now)]
    assert FollowUpAgent().next_allowed(case, now, 24) >= now + timedelta(hours=24)


def test_durable_worker_prevents_duplicate_reminders(service):
    from app.cases.automation import process_due

    case = service.store.case
    now = datetime(2026, 11, 17, 6, 30, tzinfo=timezone.utc)  # Noon IST.
    case.next_automation_at = now
    case.last_human_activity_at = now
    case.followups = [FollowUp(reason="manual", due_at=now, created_by="citizen-a")]
    assert run(process_due(service, now)) == 1
    assert len(service.store.case.reminders) == 1
    service.store.case.next_automation_at = now
    run(process_due(service, now))
    assert len(service.store.case.reminders) == 1


@pytest.mark.parametrize(
    "question,intent,node",
    [
        ("What documents do I need?", "auto", "document_verifier"),
        ("When is my next follow-up?", "auto", "follow_up"),
        ("What is happening with my case?", "auto", "case_status"),
        ("I need a human coordinator", "auto", "escalation"),
    ],
)
def test_langgraph_case_routing_read_only(service, question, intent, node):
    case = service.store.case
    result = run(
        CaseOrchestrator(service).run(
            case.id, actor(), AssistanceRequest(revision=0, question=question, intent=intent), ""
        )
    )
    assert node in result["trace"]
    assert "read_only_no_case_mutation" in result["trace"]
    assert service.store.case.revision == 0


def test_agent_apply_changes_and_cross_user_denial(service):
    case = service.store.case
    request = AssistanceRequest(
        revision=0, question="Request a human coordinator", apply_changes=True
    )
    result = run(CaseOrchestrator(service).run(case.id, actor(), request, "agent-key-123456789"))
    assert result["applied"] and service.store.case.stage == Stage.escalated
    assert service.store.case.last_workflow["intent"] == "escalation"
    with pytest.raises(HTTPException):
        run(
            CaseOrchestrator(service).run(
                case.id, actor(user_id="citizen-b"), request, "another-key-123456789"
            )
        )


def test_scheme_matcher_handoff_is_authorized_and_session_bound(service):
    from app.ai.models import MatchResponse, Profile

    calls = []

    class Matcher:
        async def match(self, request, session):
            calls.append((request, session))
            return MatchResponse(
                conversation_id="c" * 43,
                profile=Profile(),
                message="Synthetic test",
                recommendations=[],
                follow_up_questions=[],
                warnings=[],
                mode="test",
                trace=[],
            )

    async def factory():
        return Matcher()

    graph = CaseOrchestrator(service, factory, "independent-test-session-key")
    request = AssistanceRequest(
        revision=0, question="What other schemes might help?", intent="scheme_match"
    )
    result = run(graph.run(service.store.case.id, actor(), request, ""))
    assert "scheme_matcher" in result["trace"]
    assert service.store.case.scheme_id in calls[0][0].question
    assert calls[0][1] == "independent-test-session-key"
    with pytest.raises(HTTPException):
        run(graph.run(service.store.case.id, actor(user_id="another-citizen"), request, ""))
    assert len(calls) == 1
