"""Optional operator-configured adapters. Never instantiated by the in-app scheduler."""

import re
from dataclasses import dataclass
from typing import Literal

import httpx
from pydantic import Field

from app.cases.models import Strict


class OutboundNotice(Strict):
    recipient: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    language: Literal["en", "hi", "te"] = "en"
    consent: bool


@dataclass
class DeliveryReceipt:
    status: Literal["accepted", "unknown"]
    provider_id: str | None


class MessagingAdapter:
    def __init__(
        self,
        provider: Literal["twilio", "meta"],
        *,
        approved=False,
        account="",
        credential="",
        sender="",
        api_version="",
        template="",
        transport=None,
    ):
        self.provider, self.approved = provider, approved
        self.account, self.credential, self.sender = account, credential, sender
        self.api_version, self.template, self.transport = api_version, template, transport

    async def send(self, notice: OutboundNotice):
        if not self.approved or not notice.consent:
            raise RuntimeError(
                "External messaging requires explicit operator approval and recipient consent"
            )
        if not self.account or not self.credential or not self.sender:
            raise RuntimeError("External messaging credentials are unconfigured")
        try:
            async with httpx.AsyncClient(
                timeout=10, follow_redirects=False, transport=self.transport
            ) as client:
                if self.provider == "twilio":
                    if not re.fullmatch(r"AC[a-fA-F0-9]{32}", self.account):
                        raise RuntimeError("Invalid Twilio account configuration")
                    # Fixed generic text: no case IDs, addresses, documents or free-form notes.
                    from app.cases.notifications import CASE_MESSAGES

                    response = await client.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{self.account}/Messages.json",
                        auth=(self.account, self.credential),
                        data={
                            "To": notice.recipient,
                            "From": self.sender,
                            "Body": CASE_MESSAGES[notice.language],
                        },
                    )
                    response.raise_for_status()
                    provider_id = response.json()["sid"]
                elif self.provider == "meta":
                    if (
                        not re.fullmatch(r"v\d+\.\d+", self.api_version)
                        or not self.template
                        or not self.sender.isdigit()
                    ):
                        raise RuntimeError(
                            "Configure the Meta API version, phone-number ID and approved template"
                        )
                    response = await client.post(
                        f"https://graph.facebook.com/{self.api_version}/{self.sender}/messages",
                        headers={"Authorization": f"Bearer {self.credential}"},
                        json={
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": notice.recipient.lstrip("+"),
                            "type": "template",
                            "template": {
                                "name": self.template,
                                "language": {"code": notice.language},
                            },
                        },
                    )
                    response.raise_for_status()
                    provider_id = response.json()["messages"][0]["id"]
                else:
                    raise RuntimeError("Unsupported messaging provider")
            if not isinstance(provider_id, str) or not 1 <= len(provider_id) <= 512:
                raise ValueError("Invalid receipt")
            return DeliveryReceipt("accepted", provider_id)
        except httpx.ReadTimeout:
            # Provider may have accepted the message: never blindly resend and double charge.
            return DeliveryReceipt("unknown", None)
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise RuntimeError(
                "Messaging provider rejected or failed the request; no delivery is confirmed"
            ) from exc
