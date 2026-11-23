import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class NotificationProvider(Protocol):
    def delivered(self, case_id: str, reminder_id: str): ...


class InAppDevelopmentNotifications:
    """Reminder records are persisted in the case; logs contain IDs only, never contents."""

    def delivered(self, case_id, reminder_id):
        logger.info("In-app reminder persisted: case=%s reminder=%s", case_id, reminder_id)


# Future SMS/WhatsApp adapters must implement NotificationProvider and obtain explicit
# channel consent. No paid provider, credentials or transport is connected in Phase 3.
