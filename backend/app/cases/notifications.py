import logging
from typing import Protocol

logger = logging.getLogger(__name__)
CASE_MESSAGES = {
    "en": "Your assistance case has an update. Open the case for details.",
    "hi": "आपके सहायता मामले में अपडेट है। विवरण के लिए मामला खोलें।",
    "te": "మీ సహాయ అభ్యర్థనకు నవీకరణ ఉంది. వివరాల కోసం అభ్యర్థనను తెరవండి.",
}


class NotificationProvider(Protocol):
    def delivered(self, case_id: str, reminder_id: str): ...


class InAppDevelopmentNotifications:
    """Reminder records are persisted in the case; logs contain IDs only, never contents."""

    def delivered(self, case_id, reminder_id):
        logger.info("In-app reminder persisted: case=%s reminder=%s", case_id, reminder_id)


# Future SMS/WhatsApp adapters must implement NotificationProvider and obtain explicit
# channel consent. No paid provider, credentials or transport is connected in Phase 3.
