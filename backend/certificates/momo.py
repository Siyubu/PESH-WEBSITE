"""Minimal MTN MoMo Collections API client (https://momodeveloper.mtn.com)."""
import base64
import re
import time

import requests
from django.conf import settings

TIMEOUT = 20
_token = {"value": None, "expires": 0.0}


class MomoError(Exception):
    pass


def _cfg():
    return settings.MOMO


def _need(name):
    value = _cfg()[name]
    if not value:
        raise MomoError(f"MOMO_{name} is not configured")
    return value


def configured():
    c = _cfg()
    return bool(c["SUBSCRIPTION_KEY"] and c["API_USER"] and c["API_KEY"])


def _token_value():
    if _token["value"] and _token["expires"] > time.time() + 30:
        return _token["value"]
    basic = base64.b64encode(f"{_need('API_USER')}:{_need('API_KEY')}".encode()).decode()
    r = requests.post(
        f"{_cfg()['BASE_URL']}/collection/token/",
        headers={"Authorization": f"Basic {basic}", "Ocp-Apim-Subscription-Key": _need("SUBSCRIPTION_KEY")},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        raise MomoError(f"token request failed ({r.status_code})")
    data = r.json()
    _token.update(value=data["access_token"], expires=time.time() + int(data["expires_in"]))
    return _token["value"]


def _headers(extra=None):
    h = {
        "Authorization": f"Bearer {_token_value()}",
        "X-Target-Environment": _cfg()["TARGET_ENVIRONMENT"],
        "Ocp-Apim-Subscription-Key": _need("SUBSCRIPTION_KEY"),
    }
    h.update(extra or {})
    return h


def request_to_pay(*, reference, amount, currency, external_id, phone, payer_message, payee_note, callback_url=None):
    extra = {"X-Reference-Id": str(reference), "Content-Type": "application/json"}
    if callback_url:
        extra["X-Callback-Url"] = callback_url
    r = requests.post(
        f"{_cfg()['BASE_URL']}/collection/v1_0/requesttopay",
        headers=_headers(extra),
        json={
            "amount": str(amount),
            "currency": currency,
            "externalId": external_id,
            "payer": {"partyIdType": "MSISDN", "partyId": phone},
            "payerMessage": payer_message,
            "payeeNote": payee_note,
        },
        timeout=TIMEOUT,
    )
    if r.status_code != 202:
        raise MomoError(f"requesttopay failed ({r.status_code}) {r.text[:200]}")


def get_status(reference):
    """Returns {'status': 'PENDING'|'SUCCESSFUL'|'FAILED', 'amount': ..., 'reason': ...}."""
    r = requests.get(f"{_cfg()['BASE_URL']}/collection/v1_0/requesttopay/{reference}", headers=_headers(), timeout=TIMEOUT)
    if r.status_code != 200:
        raise MomoError(f"status request failed ({r.status_code})")
    return r.json()


def normalize_rwanda_phone(value):
    """0788123456 / +250788123456 / 788123456 -> 250788123456 (MTN numbers only)."""
    digits = re.sub(r"\D", "", str(value or ""))
    m = re.fullmatch(r"(?:250|0)?(7[89]\d{7})", digits)
    return f"250{m.group(1)}" if m else None
