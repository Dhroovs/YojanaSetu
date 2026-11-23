import asyncio
import json

import httpx
import pytest

from app.seva.messaging import MessagingAdapter, OutboundNotice


def test_external_channels_require_both_operator_approval_and_recipient_consent():
    message = OutboundNotice(recipient="+12025550123", consent=True)
    with pytest.raises(RuntimeError, match="approval"):
        asyncio.run(MessagingAdapter("twilio").send(message))
    with pytest.raises(RuntimeError, match="consent"):
        asyncio.run(
            MessagingAdapter("meta", approved=True).send(
                message.model_copy(update={"consent": False})
            )
        )


@pytest.mark.parametrize("provider", ["twilio", "meta"])
def test_provider_payload_is_generic_and_receipt_is_not_claimed_delivered(provider):
    calls = []

    def handle(request):
        calls.append(request)
        assert b"Aadhaar" not in request.content and b"address" not in request.content
        if provider == "meta":
            body = json.loads(request.content)
            assert body["type"] == "template" and body["recipient_type"] == "individual"
            return httpx.Response(200, json={"messages": [{"id": "synthetic-receipt"}]})
        assert request.url.host == "api.twilio.com"
        return httpx.Response(201, json={"sid": "synthetic-receipt"})

    adapter = MessagingAdapter(
        provider,
        approved=True,
        account="AC" + "0" * 32,
        credential="synthetic-not-a-secret",
        sender="12345",
        api_version="v25.0",
        template="generic_assistance_update",
        transport=httpx.MockTransport(handle),
    )
    result = asyncio.run(adapter.send(OutboundNotice(recipient="+12025550123", consent=True)))
    assert result.status == "accepted" and result.provider_id == "synthetic-receipt"
    assert len(calls) == 1


def test_ambiguous_timeout_is_not_blindly_retried_or_reported_delivered():
    calls = []

    def handle(request):
        calls.append(request)
        raise httpx.ReadTimeout("Synthetic timeout")

    adapter = MessagingAdapter(
        "twilio",
        approved=True,
        account="AC" + "0" * 32,
        credential="synthetic-not-a-secret",
        sender="12345",
        transport=httpx.MockTransport(handle),
    )
    result = asyncio.run(adapter.send(OutboundNotice(recipient="+12025550123", consent=True)))
    assert result.status == "unknown" and result.provider_id is None and len(calls) == 1
