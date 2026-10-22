"""Thin Paystack API client.

Docs: https://paystack.com/docs/api/
Only the calls this app needs are implemented.
"""
import requests
from django.conf import settings

BASE_URL = "https://api.paystack.co"
TIMEOUT = 20


class PaystackError(Exception):
    pass


def _headers():
    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError(
            "Paystack is not configured. Add PAYSTACK_SECRET_KEY to your .env file."
        )
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initialize_transaction(email, amount_kobo, reference, callback_url, plan_code="", currency="NGN"):
    """Start a transaction. `amount_kobo` is the smallest currency unit.

    When a plan_code is supplied, Paystack treats this as a subscription
    and bills the plan amount on the plan's interval.
    """
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "callback_url": callback_url,
        "currency": currency,
    }
    if plan_code:
        payload["plan"] = plan_code

    resp = requests.post(
        f"{BASE_URL}/transaction/initialize",
        json=payload, headers=_headers(), timeout=TIMEOUT,
    )
    data = _parse(resp)
    return data["data"]  # {authorization_url, access_code, reference}


def verify_transaction(reference):
    """Verify a transaction by reference. Returns the `data` object."""
    resp = requests.get(
        f"{BASE_URL}/transaction/verify/{reference}",
        headers=_headers(), timeout=TIMEOUT,
    )
    data = _parse(resp)
    return data["data"]


def _parse(resp):
    try:
        data = resp.json()
    except ValueError as exc:
        raise PaystackError(f"Invalid response from Paystack ({resp.status_code}).") from exc
    if not data.get("status"):
        raise PaystackError(data.get("message", "Paystack request failed."))
    return data
