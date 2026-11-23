"""External channel contract. No SMS/WhatsApp transport or billing is connected."""

from typing import Literal, Protocol


class ExternalChannel(Protocol):
    async def send_template(self, recipient_reference: str, template: str, language: str) -> str:
        """Return a delivery ID only after an approved provider accepts delivery."""
        ...


class DisabledChannel:
    def __init__(self, kind: Literal["sms", "whatsapp"]):
        self.kind = kind

    async def send_template(self, recipient_reference: str, template: str, language: str) -> str:
        raise RuntimeError(f"{self.kind} is disabled; approved provider configuration is required")
