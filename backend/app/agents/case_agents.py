from datetime import timedelta
from zoneinfo import ZoneInfo

from app.cases.models import TERMINAL, ReviewStatus


class DocumentVerifier:
    """Technical completeness assistance only; never authenticates legal identity."""

    def analyze(self, case, now):
        items = []
        for item in case.checklist:
            documents = [
                d
                for d in case.documents
                if d.item_id == item.id and not d.deleted_at and d.expires_at > now
            ]
            accepted = any(d.review_status == ReviewStatus.accepted for d in documents)
            status = (
                "accepted_for_assistance_checklist"
                if accepted
                else (documents[-1].review_status.value if documents else "missing")
            )
            items.append(
                {
                    "id": item.id,
                    "label": item.label,
                    "status": status,
                    "source_ids": item.source_ids,
                    "is_demo": item.is_demo,
                }
            )
        missing = [i["id"] for i in items if i["status"] in {"missing", "unreadable"}]
        ready = case.checklist_verified and all(
            i["status"] == "accepted_for_assistance_checklist" for i in items
        )
        return {
            "agent": "document_verifier",
            "items": items,
            "missing_item_ids": missing,
            "ready_for_human_review": ready,
            "checklist_verified": case.checklist_verified,
            "doorstep_suggestion": "You may request a consented SevaSetu document-assistance visit."
            if missing
            else None,
            "next_action": "A coordinator can review the assistance task."
            if ready
            else "Confirm the source checklist with a coordinator."
            if not case.checklist_verified
            else "Upload missing items; readable files still require a human checklist review.",
            "disclaimer": "Technical readability is not authenticity, legal validity or KYC.",
        }


class FollowUpAgent:
    def analyze(self, case, now):
        pending = sorted(
            [f for f in case.followups if f.status == "scheduled"], key=lambda f: f.due_at
        )
        return {
            "agent": "follow_up",
            "next_follow_up": pending[0].model_dump(mode="json") if pending else None,
            "unacknowledged_reminders": [
                r.id for r in case.reminders if case.owner_id not in r.acknowledged_by
            ],
            "next_action": "Review the next scheduled internal follow-up."
            if pending
            else "Request or schedule an internal follow-up.",
            "official_status": "Not connected to a government status integration.",
        }

    def next_allowed(self, case, now, frequency_hours):
        local = now.astimezone(ZoneInfo("Asia/Kolkata"))
        start, end = case.preferences.quiet_start, case.preferences.quiet_end
        quiet = start != end and (
            start <= local.hour < end if start < end else local.hour >= start or local.hour < end
        )
        allowed = now
        if quiet:
            morning = local.replace(hour=end, minute=0, second=0, microsecond=0)
            if morning <= local:
                morning += timedelta(days=1)
            allowed = morning.astimezone(now.tzinfo)
        if case.reminders:
            allowed = max(allowed, case.reminders[-1].created_at + timedelta(hours=frequency_hours))
        return allowed


class EscalationAgent:
    def __init__(self, settings):
        self.settings = settings

    def analyze(self, case, now, explicit=False):
        triggers = []
        if case.stage in TERMINAL:
            return {
                "agent": "escalation",
                "triggers": [],
                "next_action": "Assistance task is inactive.",
            }
        if explicit:
            triggers.append({"reason": "human_assistance_requested", "severity": "normal"})
        if now - case.last_human_activity_at >= timedelta(
            days=self.settings.escalation_inactivity_days
        ):
            triggers.append({"reason": "case_inactivity", "severity": "normal"})
        missing = DocumentVerifier().analyze(case, now)["missing_item_ids"]
        if (
            missing
            and sum(r.reason == "missing_documents" for r in case.reminders)
            >= self.settings.missing_document_reminder_limit
        ):
            triggers.append({"reason": "repeated_missing_documents", "severity": "high"})
        if any(
            not d.deleted_at
            and d.review_status == ReviewStatus.human
            and now - d.created_at
            >= timedelta(hours=self.settings.document_review_escalation_hours)
            for d in case.documents
        ):
            triggers.append({"reason": "unresolved_document_review", "severity": "high"})
        if any(
            s in case.missing_information for s in ("conflicting_information", "coordinator_flag")
        ):
            triggers.append({"reason": "conflicting_information", "severity": "high"})
        return {
            "agent": "escalation",
            "triggers": triggers,
            "next_action": "Refer to an authorized internal coordinator."
            if triggers
            else "No configured escalation condition is currently met.",
            "disclaimer": "Internal human referral, not a complaint to a government department.",
        }
