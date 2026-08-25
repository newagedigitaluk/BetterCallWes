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
from datetime import datetime, timedelta


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


# ─────────────────────────────────────────────────────────────────────────
# Schedule tokens — "book this job that already exists"
#
# Different problem to BookingToken above. These go to customers whose job
# is already in SM8 but has no diary slot yet (contract work dropped in by
# YourRepair/Hometree, overdue annual services, etc). They pick a slot and
# we write a jobactivity onto THAT job — we never create a new one, which
# matters because on contract work the bill goes to the provider, not the
# occupier.
#
# Payload carries "k":"sched" so a manage-booking token can't be replayed
# here (and vice versa) even though both are signed with the same secret.
# There's no slot_iso (no slot yet) and no email_h — several of these jobs
# have no email on the contact at all, so it can't be a required field.
# ─────────────────────────────────────────────────────────────────────────

SCHEDULE_TOKEN_KIND = "sched"


@dataclass(frozen=True)
class ScheduleToken:
    job_uuid: str
    exp: int


def make_schedule_token(*, secret: str, job_uuid: str, expires_at: datetime) -> str:
    """Mint a signed 'pick your slot' token for an existing, unscheduled job."""
    if not secret:
        raise ValueError("secret required to sign tokens")
    if not job_uuid:
        raise ValueError("job_uuid required")
    payload = {
        "k": SCHEDULE_TOKEN_KIND,
        "job_uuid": job_uuid,
        "exp": int(expires_at.timestamp()),
    }
    payload_b = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url(payload_b)
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_schedule_token(token: str, *, secret: str) -> ScheduleToken:
    """Verify signature, kind and expiry. Raises TokenInvalid / TokenExpired."""
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

    if payload.get("k") != SCHEDULE_TOKEN_KIND:
        raise TokenInvalid("not a scheduling token")
    if not {"job_uuid", "exp"}.issubset(payload):
        raise TokenInvalid("payload missing required fields")
    if int(payload["exp"]) < int(time.time()):
        raise TokenExpired("this booking link has expired")

    return ScheduleToken(job_uuid=str(payload["job_uuid"]), exp=int(payload["exp"]))


# ─────────────────────────────────────────────────────────────────────────
# Compact schedule tokens
#
# The JSON-payload token above is ~172 characters. Fine inside a WhatsApp
# button (the URL is hidden behind the button text) but awful in an SMS,
# where it pushes the message to three billed segments and makes a genuine
# message look like phishing.
#
# This packs the same meaning into 35 characters with no server-side
# storage, so there's no code->token table to keep in sync:
#
#   16 bytes  job uuid (hex, dashes stripped)
#    2 bytes  expiry as days since 2020-01-01 (big-endian)
#    8 bytes  truncated HMAC-SHA256 over the above
#   = 26 bytes -> 35 chars base64url
#
# On the 8-byte signature: 64 bits, and every forgery attempt costs the
# attacker a round trip to our server. The prize is booking a slot on
# someone else's job, which the endpoint further guards (already-scheduled
# and completed jobs are refused). Not worth more bytes.
# ─────────────────────────────────────────────────────────────────────────

_EPOCH = datetime(2020, 1, 1)
_SIG_BYTES = 8


def _short_sig(payload: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()[:_SIG_BYTES]


def make_short_schedule_token(*, secret: str, job_uuid: str, expires_at: datetime) -> str:
    """Compact, storage-free scheduling token. Same guarantees as
    make_schedule_token, ~5x shorter."""
    if not secret:
        raise ValueError("secret required to sign tokens")
    raw = uuid_bytes = bytes.fromhex(job_uuid.replace("-", ""))
    if len(uuid_bytes) != 16:
        raise ValueError(f"job_uuid must be a 16-byte uuid, got {len(uuid_bytes)}")
    days = (expires_at - _EPOCH).days
    if not 0 <= days <= 0xFFFF:
        raise ValueError("expiry out of representable range")
    payload = raw + days.to_bytes(2, "big")
    return _b64url(payload + _short_sig(payload, secret))


def verify_short_schedule_token(token: str, *, secret: str) -> ScheduleToken:
    """Verify a compact token. Raises TokenInvalid / TokenExpired."""
    if not secret:
        raise TokenInvalid("server has no signing secret configured")
    try:
        blob = _b64url_decode(token)
    except Exception:  # noqa: BLE001
        raise TokenInvalid("malformed token") from None
    if len(blob) != 18 + _SIG_BYTES:
        raise TokenInvalid("malformed token")

    payload, sig = blob[:18], blob[18:]
    if not hmac.compare_digest(_short_sig(payload, secret), sig):
        raise TokenInvalid("signature mismatch")

    job_hex = payload[:16].hex()
    job_uuid = f"{job_hex[0:8]}-{job_hex[8:12]}-{job_hex[12:16]}-{job_hex[16:20]}-{job_hex[20:32]}"
    exp_dt = _EPOCH + timedelta(days=int.from_bytes(payload[16:18], "big"))
    if exp_dt < datetime.now():
        raise TokenExpired("this booking link has expired")
    return ScheduleToken(job_uuid=job_uuid, exp=int(exp_dt.timestamp()))
