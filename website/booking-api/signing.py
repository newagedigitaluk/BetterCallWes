"""HMAC-signed magic-link tokens for self-serve booking management.

Customers get a long token in their confirmation email/SMS:
  https://bettercallwes.co.uk/manage-booking.html?t=<token>

The token is opaque to the client but server-verifiable. It contains:
  - job_uuid:  which SM8 job this link manages
  - slot_iso:  the slot at issue time (sanity check)
  - email_h:   first 8 hex chars of SHA-256(customer_email) — prevents
               token reuse across customers (we don't need the full
               email to identify; the hash is enough)
  - exp:       unix timestamp; we reject after this point

Token format:  base64url(payload_json) + "." + hex(hmac_sha256(payload, secret))

Why not JWT lib?  We need exactly one feature (HMAC sign/verify),
no algorithm negotiation, no key rotation, no spec compliance. 30
lines of stdlib does the job.

Security caveats:
  - Anyone with the token can manage that booking (no second factor).
    Mitigations: the URL is sent only to the verified email + phone,
    the token expires at slot start, and the 12h notice rule limits
    last-minute mischief.
  - MAGIC_LINK_SECRET must NEVER be committed; rotate in Coolify if
    you suspect leak (any old tokens become invalid).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from datetime import datetime


class TokenError(Exception):
    """Base — distinct subclasses below for finer-grained handling."""


class TokenInvalid(TokenError):
    """Signature didn't verify, JSON malformed, etc."""


class TokenExpired(TokenError):
    """Token was valid once but its `exp` is in the past."""


@dataclass(frozen=True)
class BookingToken:
    job_uuid: str
    slot_iso: str       # ISO string of the slot start when the token was issued
    email_hash: str     # 8 hex chars
    exp: int            # unix seconds


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def email_hash(email: str) -> str:
    """First 8 hex chars of SHA-256(lowercased email)."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:8]


def make_token(
    *,
    secret: str,
    job_uuid: str,
    slot_start: datetime,
    customer_email: str,
) -> str:
    """Mint a signed token. `exp` is automatically set to slot_start."""
    if not secret:
        raise ValueError("secret required to sign tokens")
    payload = {
        "job_uuid": job_uuid,
        "slot_iso": slot_start.isoformat(timespec="seconds"),
        "email_h": email_hash(customer_email),
        "exp": int(slot_start.timestamp()),
    }
    payload_b = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url(payload_b)
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str, *, secret: str) -> BookingToken:
    """Verify signature + expiry. Raises TokenInvalid / TokenExpired."""
    if not secret:
        raise TokenInvalid("server has no signing secret configured")
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        raise TokenInvalid("malformed token") from None

    expected_sig = hmac.new(
        secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        raise TokenInvalid("signature mismatch")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError) as e:
        raise TokenInvalid(f"payload decode failed: {e}") from None

    required = {"job_uuid", "slot_iso", "email_h", "exp"}
    if not required.issubset(payload):
        raise TokenInvalid("payload missing required fields")

    if int(payload["exp"]) < int(time.time()):
        raise TokenExpired("link has expired (booking has already started or passed)")

    return BookingToken(
        job_uuid=str(payload["job_uuid"]),
        slot_iso=str(payload["slot_iso"]),
        email_hash=str(payload["email_h"]),
        exp=int(payload["exp"]),
    )
