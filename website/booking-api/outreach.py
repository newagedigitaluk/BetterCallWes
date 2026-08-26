#!/usr/bin/env python3
"""Batch "pick your slot" outreach for jobs that are already in ServiceM8.

The problem this solves: contract work from YourRepair (who now own
Hometree) lands in SM8 with no diary slot, and chasing 15 people by phone
is a day Wes doesn't have. Each job gets a signed link, the customer picks
their own slot, and the slot is written to the EXISTING job.

Channels, in order:
  1. WhatsApp template  — needs an approved template AND a way to auth to
                          the ServiceHQ add-on (see WHATSAPP AUTH below)
  2. SMS                — works today via the SM8 API, no extra auth
  3. Nothing            — landline-only contacts are reported, not messaged

Fallback is OUTCOME-based, not delivery-based. WhatsApp Cloud API has no
"does this number have WhatsApp" lookup, so you only learn it failed after
the fact. Rather than plumb delivery webhooks between two systems, we just
ask the question that actually matters: is it booked yet? If not, chase.
That covers every failure mode identically — no WhatsApp, wrong number,
delivered but ignored.

The chase ladder, run by --followup (see plan_followups):
  day 0                     WhatsApp  -> occupier
  +2 working days           SMS       -> occupier
  +5 working days           SMS       -> landlord   (a different person,
                                                     not a third nag)
  after that                stop, and Wes gets a call list

Nobody gets more than MAX_TOUCHES_PER_PERSON automated messages. Spam
reports sink a WhatsApp template's quality rating, and a rating drop
costs far more than one unbooked service.

Usage:
    python outreach.py --list                 # who's eligible, no sending
    python outreach.py --dry-run              # render every message, no sending
    python outreach.py --send --channel sms   # actually send
    python outreach.py --followup --send      # SMS sweep for the unbooked

Env required:
    SERVICEM8_API_KEY   read jobs, send SMS
    MAGIC_LINK_SECRET   MUST match the booking API's secret, or the links
                        it generates will not verify. Lives in Coolify.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from signing import make_short_schedule_token  # noqa: E402

SM8 = "https://api.servicem8.com/api_1.0"
API_KEY = os.environ.get("SERVICEM8_API_KEY", "")
MAGIC_LINK_SECRET = os.environ.get("MAGIC_LINK_SECRET", "")
PUBLIC_BASE = os.environ.get("PUBLIC_SITE_BASE", "https://bettercallwes.co.uk").rstrip("/")

LINK_TTL_DAYS = int(os.environ.get("SCHEDULE_LINK_TTL_DAYS", "60"))

# ── Chase cadence ───────────────────────────────────────────────────
# Touch 1  day 0            WhatsApp -> occupier
# Touch 2  +2 working days  SMS      -> occupier   (channel switch is the
#                                       real lever: a second WhatsApp is
#                                       useless if the first never landed)
# Touch 3  +5 working days  SMS      -> LANDLORD   (a different person, not
#                                       a third nag at someone ignoring us)
# then     stop            -> Wes rings them
#
# Two automated touches max per person. A third is where spam reports come
# from, and on WhatsApp those hit the template quality rating — lose that
# and the whole channel goes, over eleven gas safety checks.
FOLLOWUP_WORKING_DAYS = int(os.environ.get("FOLLOWUP_WORKING_DAYS", "2"))
ESCALATE_WORKING_DAYS = int(os.environ.get("ESCALATE_WORKING_DAYS", "5"))
MAX_TOUCHES_PER_PERSON = int(os.environ.get("MAX_TOUCHES_PER_PERSON", "2"))

# Only chase work that is actually late or nearly due. Something not due
# for weeks isn't being ignored, it just isn't due — one message, no chase.
CHASE_IF_DUE_WITHIN_DAYS = int(os.environ.get("CHASE_IF_DUE_WITHIN_DAYS", "14"))

# A booking link at 7am on a Sunday from an unknown number gets deleted.
SEND_HOUR_FROM = int(os.environ.get("SEND_HOUR_FROM", "9"))
SEND_HOUR_TO = int(os.environ.get("SEND_HOUR_TO", "18"))
WHATSAPP_TEMPLATE = os.environ.get("WHATSAPP_TEMPLATE", "service_due_book_slot")

STATE_PATH = Path(__file__).parent / "outreach-state.json"

# SM8 category -> what we call it to the customer. Deliberately the
# customer's words, not SM8's: "Gas Safety Check" means nothing to someone
# who was told they're getting a safety certificate.
SERVICE_LABEL = {
    "40777738-5689-4138-b470-1bd946fec30b": "gas safety check",
    "506bcb7e-579c-42cf-aef2-1bd946440eeb": "annual boiler service",
    "04362e23-b01b-4b3b-883c-1bdde302fceb": "boiler service and gas safety check",
}
PROVIDER_BADGES = {"YourRepair", "Hometree"}

# Hard manual override. Set this badge in SM8 on any job that must never be
# auto-chased — e.g. Wes has already spoken to them, or there's a dispute.
# Beats the due-date logic below, no questions asked.
NO_CHASE_BADGE = "No Auto-Chase"

# Don't chase work that isn't due yet. The provider's portal shows a due
# date and we copy it into the job description ("Due September 2026",
# "Due 01/09/2026"). Chasing someone four months early reads as pestering,
# and at least twice the portal's date has been wrong where the customer
# knew better — so a corrected date in the description wins.
DUE_WITHIN_DAYS = int(os.environ.get("DUE_WITHIN_DAYS", "30"))

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}


def parse_due(desc: str) -> datetime | None:
    """Pull a due date out of the job description. None = unknown, which we
    treat as due now rather than silently skipping real work."""
    m = re.search(r"Due\s+(\d{1,2})/(\d{1,2})/(\d{4})", desc or "", re.I)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        try:
            return datetime(y, mo, d)
        except ValueError:
            return None
    m = re.search(r"Due\s+([A-Za-z]+)\s+(\d{4})", desc or "", re.I)
    if m and m.group(1).lower() in _MONTHS:
        return datetime(int(m.group(2)), _MONTHS[m.group(1).lower()], 1)
    return None


# ─────────────────────────── SM8 plumbing ───────────────────────────

def sm8(method: str, path: str, body: dict | None = None, retries: int = 5):
    for attempt in range(retries):
        req = urllib.request.Request(
            SM8 + path, method=method,
            headers={"X-Api-Key": API_KEY, "Accept": "application/json",
                     "Content-Type": "application/json"},
            data=(json.dumps(body).encode() if body is not None else None),
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode()
                return r.status, (json.loads(raw) if raw.strip() else None)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return e.code, e.read().decode()[:200]
    return 0, "exhausted retries"


def working_days_between(a: datetime, b: datetime) -> int:
    """Mon-Fri days from a to b. A 48h timer on a Friday send chases them
    on Sunday, which reads as pushy from someone they've never met."""
    if b <= a:
        return 0
    days, cur = 0, a.date()
    while cur < b.date():
        cur += timedelta(days=1)
        if cur.weekday() < 5:
            days += 1
    return days


def within_sending_hours(now: datetime | None = None) -> tuple[bool, str]:
    now = now or datetime.now()
    if now.weekday() >= 5:
        return False, "weekend"
    if not (SEND_HOUR_FROM <= now.hour < SEND_HOUR_TO):
        return False, f"outside {SEND_HOUR_FROM}:00-{SEND_HOUR_TO}:00"
    return True, ""


def has_replied(job_uuid: str, since: datetime) -> bool:
    """Did the customer come back to us on any channel since we messaged?

    Chasing someone who has already replied is worse than never messaging
    them. SM8 records direction on both SMS and email, and the ServiceHQ
    add-on routes WhatsApp into the job diary as notes, so all three are
    visible here without touching the add-on's API.
    """
    stamp = since.strftime("%Y-%m-%d %H:%M:%S")
    for ep in ("sms", "email"):
        _, rows = sm8("GET", f"/{ep}.json?%24filter=related_object_uuid%20eq%20{job_uuid}")
        for r in (rows or []):
            if r.get("direction") == "inbound" and str(r.get("timestamp") or "") > stamp:
                return True
    _, notes = sm8("GET", f"/note.json?%24filter=related_object_uuid%20eq%20{job_uuid}")
    for n in (notes or []):
        if str(n.get("create_date") or "") > stamp and "whatsapp" in (n.get("note") or "").lower():
            return True
    return False


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"sent": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


# ─────────────────────────── Job selection ───────────────────────────

def normalise_mobile(raw: str) -> str | None:
    """UK mobile in E.164, or None if it isn't a mobile at all.

    Landlines are a real case here (one of these customers is a Winchester
    01962 number). Returning None rather than a best guess keeps us from
    firing SMS at a phone that can't receive it.
    """
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("+44"):
        digits = "0" + digits[3:]
    elif digits.startswith("44") and len(digits) > 11:
        digits = "0" + digits[2:]
    if re.fullmatch(r"07\d{9}", digits):
        return "+44" + digits[1:]
    return None


SUB_PREMISE = re.compile(r"^\s*(flat|apt|apartment|unit|room|annexe?)\b", re.I)


def short_address(full: str) -> str:
    """First meaningful line of an address, for "your service at ___".

    Naively taking the first comma-separated part gives "Flat 15", which
    tells the customer nothing and looks like a mail-merge failure. When
    the first part is a sub-premise, keep the street with it.
    """
    parts = [p.strip() for p in (full or "").replace("\n", ",").split(",") if p.strip()]
    if not parts:
        return ""
    if SUB_PREMISE.match(parts[0]) and len(parts) > 1:
        return f"{parts[0]}, {parts[1]}"
    return parts[0]


def eligible_jobs(badge_names: dict[str, str]) -> list[dict]:
    """Jobs that still need a slot: active, not completed, nothing in the diary."""
    _, jobs = sm8("GET", "/job.json")
    if not isinstance(jobs, list):
        raise SystemExit(f"could not list jobs: {jobs}")

    out = []
    for j in jobs:
        if j.get("active") != 1:
            continue
        if (j.get("status") or "") in ("Completed", "Unsuccessful", "Quote"):
            continue
        if (j.get("category_uuid") or "") not in SERVICE_LABEL:
            continue

        # Provider: badge first (what Wes maintains in SM8), description as
        # the safety net so a missing badge never blocks a send.
        provider = None
        no_chase = False
        try:
            for bid in json.loads(j.get("badges") or "[]"):
                nm = badge_names.get(bid)
                if nm in PROVIDER_BADGES:
                    provider = nm
                elif nm == NO_CHASE_BADGE:
                    no_chase = True
        except (json.JSONDecodeError, TypeError):
            pass
        if no_chase:
            continue
        if not provider:
            m = re.search(r"\b(YourRepair|Hometree)\b", j.get("job_description") or "")
            provider = m.group(1) if m else None
        if not provider:
            continue  # not contract work, leave it alone

        # Not due for a while yet? Leave them be.
        due = parse_due(j.get("job_description") or "")
        if due and due > datetime.now() + timedelta(days=DUE_WITHIN_DAYS):
            continue

        # Already in the diary? Then there's nothing to chase.
        _, acts = sm8("GET", f"/jobactivity.json?%24filter=job_uuid%20eq%20{j['uuid']}")
        if isinstance(acts, list) and any(
            str(a.get("active", "1")) in ("1", "True", "true")
            and str(a.get("activity_was_scheduled", "1")) in ("1", "True", "true")
            for a in acts
        ):
            continue

        # Occupier first, landlord (Property Manager) as fallback — several
        # of these properties are tenanted and the landlord authorises access.
        _, contacts = sm8("GET", f"/jobcontact.json?%24filter=job_uuid%20eq%20{j['uuid']}")
        contacts = [c for c in (contacts or []) if c.get("active") == 1]
        occupier = next((c for c in contacts if (c.get("type") or "") == "JOB"), None)
        landlord = next((c for c in contacts if (c.get("type") or "") == "Property Manager"), None)
        target = occupier or landlord
        if not target:
            continue

        mobile = normalise_mobile(target.get("mobile") or target.get("phone") or "")
        fallback_mobile = None
        if landlord and landlord is not target:
            fallback_mobile = normalise_mobile(landlord.get("mobile") or landlord.get("phone") or "")

        out.append({
            "job_uuid": j["uuid"],
            "job_ref": j.get("generated_job_id"),
            "provider_ref": j.get("purchase_order_number") or "",
            "provider": provider,
            "service": SERVICE_LABEL[j["category_uuid"]],
            "address_short": short_address(j.get("job_address") or ""),
            "first": (target.get("first") or "").strip(),
            "mobile": mobile,
            "email": (target.get("email") or "").strip(),
            "landlord_mobile": fallback_mobile,
            "_desc": j.get("job_description") or "",
        })
    return out


# ─────────────────────────── Message building ───────────────────────────

def schedule_token(job_uuid: str) -> str:
    """Just the signed token. The WhatsApp button is defined as
    https://bettercallwes.co.uk/s/{{1}}, so the parameter is the variable
    part only; passing the whole URL would produce .../s/https://..."""
    if not MAGIC_LINK_SECRET:
        raise SystemExit("MAGIC_LINK_SECRET is not set.")
    return make_short_schedule_token(
        secret=MAGIC_LINK_SECRET,
        job_uuid=job_uuid,
        expires_at=datetime.now() + timedelta(days=LINK_TTL_DAYS),
    )


def schedule_link(job_uuid: str) -> str:
    if not MAGIC_LINK_SECRET:
        raise SystemExit(
            "MAGIC_LINK_SECRET is not set. Links generated without the SAME secret "
            "the booking API uses will fail to verify. Pull it from Coolify."
        )
    tok = make_short_schedule_token(
        secret=MAGIC_LINK_SECRET,
        job_uuid=job_uuid,
        expires_at=datetime.now() + timedelta(days=LINK_TTL_DAYS),
    )
    return f"{PUBLIC_BASE}/s/{tok}"


def whatsapp_params(job: dict) -> list[str]:
    """Body params for template `service_due_book_slot`.
    Order must match the template exactly: name, provider, service, address."""
    return [job["first"] or "there", job["provider"], job["service"], job["address_short"]]


def sms_text(job: dict, link: str) -> str:
    """Provider named first — these customers have never heard of Wes."""
    if (job.get("_touch") or {}).get("to") == "landlord":
        # Different person, different framing: they are not the occupier and
        # may not know the tenant has been asked already.
        return (
            f"Hi, it's Wes from Better Call Wes, Gas Safe engineer working for "
            f"{job['provider']}. I need to book the {job['service']} at "
            f"{job['address_short']} and haven't been able to reach the occupier. "
            f"Could you pick a time here: {link}"
        )
    return (
        f"Hi {job['first'] or 'there'}, it's Wes from Better Call Wes, Gas Safe "
        f"engineer working for {job['provider']}. They've passed your details over "
        f"for your {job['service']} at {job['address_short']}. "
        f"Pick a time here: {link}"
    )


# ─────────────────────────── Senders ───────────────────────────

SMS_ENDPOINT = "https://api.servicem8.com/platform_service_sms"

# ── ServiceHQ WhatsApp add-on ───────────────────────────────────────
SERVICEHQ_SEND_URL = os.environ.get(
    "SERVICEHQ_SEND_URL", "https://wa.servicehq.co.uk/api/service/send-template")
SERVICEHQ_KEY = os.environ.get("SERVICEHQ_KEY", "")
WHATSAPP_LANG = os.environ.get("WHATSAPP_TEMPLATE_LANG", "en_GB")

# The add-on allows 5 sends a minute per tenant and counts FAILURES against
# the same budget. Pacing below that ceiling is cheaper than discovering it:
# a burst spends its allowance on 429s, and those 429s are themselves
# counted, so the batch digs its own hole. 13s leaves headroom for a retry.
WHATSAPP_MIN_INTERVAL_SECONDS = float(os.environ.get("WHATSAPP_MIN_INTERVAL", "13"))
WHATSAPP_MAX_ATTEMPTS = int(os.environ.get("WHATSAPP_MAX_ATTEMPTS", "3"))
WHATSAPP_RETRY_BASE_SECONDS = int(os.environ.get("WHATSAPP_RETRY_BASE", "20"))


def send_sms(job: dict, link: str) -> tuple[int, str]:
    """Send via platform_service_sms, NOT /api_1.0/sms.json.

    sms.json is read-only: GET lists the message history, POST returns
    "sms is not an authorised object type" and sends nothing. That error
    reads like a permissions problem and it isn't; the same API key works
    fine here. Sending lives on a separate platform service endpoint,
    which is what ServiceM8's own n8n node calls.

    Body shape and the X-API-Key header both match that node.
    """
    target = (job.get("_touch") or {}).get("mobile") or job["mobile"]
    body = {
        "to": target,
        "message": sms_text(job, link),
        "regardingJobUUID": job["job_uuid"],
    }
    req = urllib.request.Request(
        SMS_ENDPOINT,
        method="POST",
        data=json.dumps(body).encode(),
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()[:200].decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200].decode()
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:120]


def whatsapp_preview(job: dict) -> str:
    """What the customer actually reads, for the ServiceM8 thread.

    Without this the job shows "[template: service_due_book_slot]", which
    tells whoever opens the job nothing. Mirrors the approved template body.

    The provider is named once, not twice. An earlier draft opened with
    "I carry out work on behalf of X" and then repeated X as the source of
    the details, which reads better but uses {{2}} twice. WhatsApp Manager
    refuses to submit a template that reuses a variable, silently, by
    greying out the button. The API allows it; the form does not.
    """
    return (
        f"Hi {job['first'] or 'there'}, this is Wes from Better Call Wes. I'm a "
        f"Gas Safe registered engineer.\n\n"
        f"{job['provider']} have passed your details over so I can complete your "
        f"{job['service']} at {job['address_short']}.\n\n"
        "Tap below to pick a day and time that suits you. It takes about a "
        "minute and there's no need to ring anyone."
    )


def send_whatsapp(job: dict, link: str) -> tuple[int, str]:
    """Send the approved template through the ServiceHQ add-on.

    Retry policy is dictated by the add-on's rate limiter: failed attempts
    count against the same budget as successful ones, so a tight retry loop
    turns one 502 into a run of 429s and takes the rest of the batch down
    with it. Retries are therefore few, spaced, and only for the statuses
    the add-on documents as retryable.

      429  rate limited     -> wait Retry-After, retry
      503  Meta unreachable -> back off, retry (approval could not be checked)
      502  Meta refused it  -> one spaced retry, then give up
      400/401/409           -> never retry, the call or the state is wrong
    """
    if not SERVICEHQ_KEY:
        return 0, ("SERVICEHQ_KEY not set — issue one with "
                   "POST /api/admin/service-key and put it in .env")

    target = (job.get("_touch") or {}).get("mobile") or job["mobile"]
    payload = {
        "to": target,
        "template": WHATSAPP_TEMPLATE,
        "language": WHATSAPP_LANG,
        "bodyParams": whatsapp_params(job),
        "urlButtonParam": schedule_token(job["job_uuid"]),
        "jobUuid": job["job_uuid"],
        "preview": whatsapp_preview(job),
    }

    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(
            SERVICEHQ_SEND_URL,
            method="POST",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {SERVICEHQ_KEY}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status, r.read()[:200].decode()
        except urllib.error.HTTPError as e:
            detail = e.read()[:200].decode()
            if attempt > WHATSAPP_MAX_ATTEMPTS:
                return e.code, detail
            if e.code == 429:
                # Trust their number rather than guessing; it is counted
                # from the same audit table the limiter reads.
                wait = int(e.headers.get("Retry-After") or 60)
                print(f"    rate limited, waiting {wait}s")
                time.sleep(min(wait, 3600))
                continue
            if e.code in (502, 503):
                wait = WHATSAPP_RETRY_BASE_SECONDS * attempt
                print(f"    HTTP {e.code}, retrying in {wait}s")
                time.sleep(wait)
                continue
            return e.code, detail           # 400/401/409: no retry
        except Exception as e:  # noqa: BLE001
            if attempt > WHATSAPP_MAX_ATTEMPTS:
                return 0, str(e)[:120]
            time.sleep(WHATSAPP_RETRY_BASE_SECONDS * attempt)


# ─────────────────────────── Chase planner ───────────────────────────

def plan_followups(jobs: list[dict], state: dict) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Decide who gets chased, who gets escalated, and who needs Wes.

    Returns (to_send, needs_human). Jobs in to_send carry a "_touch" dict
    describing which touch this is and who it goes to.
    """
    out: list[dict] = []
    human: list[tuple[dict, str]] = []
    now = datetime.now()

    for j in jobs:
        rec = state["sent"].get(j["job_uuid"])
        if not rec:
            continue  # never had touch 1; the normal run handles it

        touches = rec.get("touches") or [{"at": rec.get("at", 0), "channel": rec.get("channel", "sms"),
                                          "to": "occupier"}]
        last = datetime.fromtimestamp(max(t["at"] for t in touches))
        # Look for replies since the FIRST touch, not the last. Checking from
        # the last one would miss someone who answered touch 1 late, after
        # touch 2 had already gone out.
        first = datetime.fromtimestamp(min(t["at"] for t in touches))
        wd = working_days_between(last, now)

        # Not actually late? Then there is nothing to chase. One message
        # was enough; it isn't overdue, they just haven't got to it.
        due = parse_due(j.get("_desc", "") or "")
        if due and (due - now).days > CHASE_IF_DUE_WITHIN_DAYS:
            continue

        if has_replied(j["job_uuid"], first):
            human.append((j, "customer replied - needs a human, not another chase"))
            continue

        to_occupier = [t for t in touches if t.get("to") == "occupier"]

        if len(to_occupier) < MAX_TOUCHES_PER_PERSON:
            if wd >= FOLLOWUP_WORKING_DAYS:
                j["_touch"] = {"n": len(touches) + 1, "to": "occupier", "mobile": j["mobile"]}
                out.append(j)
            continue

        # Occupier has had their two. Try the landlord once — a different
        # person who can actually authorise access, not a third nag.
        if not any(t.get("to") == "landlord" for t in touches):
            if wd >= (ESCALATE_WORKING_DAYS - FOLLOWUP_WORKING_DAYS):
                if j.get("landlord_mobile") and j["landlord_mobile"] != j["mobile"]:
                    j["_touch"] = {"n": len(touches) + 1, "to": "landlord",
                                   "mobile": j["landlord_mobile"]}
                    out.append(j)
                else:
                    human.append((j, "no landlord number - Wes to call"))
            continue

        human.append((j, "chased twice plus landlord - Wes to call"))

    return out, human


# ─────────────────────────── Main ───────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="show eligible jobs only")
    ap.add_argument("--dry-run", action="store_true", help="render messages, send nothing")
    ap.add_argument("--send", action="store_true", help="actually send")
    ap.add_argument("--channel", choices=["sms", "whatsapp", "auto"], default="sms",
                    help="auto: WhatsApp if the template is approved, else SMS")
    ap.add_argument("--notify", action="store_true",
                    help="Telegram summary when the run finishes (for cron)")
    ap.add_argument("--followup", action="store_true",
                    help="chase the unbooked: SMS at +%d working days, landlord at +%d"
                         % (FOLLOWUP_WORKING_DAYS, ESCALATE_WORKING_DAYS))
    args = ap.parse_args()

    if not API_KEY:
        raise SystemExit("SERVICEM8_API_KEY not set")

    _, badges = sm8("GET", "/badge.json")
    badge_names = {b["uuid"]: b["name"] for b in (badges or [])}

    jobs = eligible_jobs(badge_names)
    state = load_state()

    needs_human: list[tuple[dict, str]] = []
    if args.followup:
        jobs, needs_human = plan_followups(jobs, state)
    elif not args.list:
        jobs = [j for j in jobs if j["job_uuid"] not in state["sent"]]

    print(f"{'job':<6} {'ref':<8} {'provider':<11} {'service':<34} {'contact':<14} {'mobile'}")
    print("-" * 100)
    for j in jobs:
        print(f"{j['job_ref']:<6} {j['provider_ref']:<8} {j['provider']:<11} "
              f"{j['service']:<34} {j['first'][:13]:<14} {j['mobile'] or '(no mobile)'}")
    print(f"\n{len(jobs)} eligible")

    no_mobile = [j for j in jobs if not j["mobile"]]
    if no_mobile:
        print(f"\n{len(no_mobile)} cannot be texted (landline or missing) — needs email or a call:")
        for j in no_mobile:
            extra = f" landlord: {j['landlord_mobile']}" if j["landlord_mobile"] else ""
            print(f"  #{j['job_ref']} {j['first']} {j['email'] or '(no email)'}{extra}")

    if args.list:
        return

    if needs_human:
        print(f"\n{len(needs_human)} need YOU, not another message:")
        for j, why in needs_human:
            print(f"  #{j['job_ref']} {j['first']:<12} {j['mobile'] or '(no mobile)':<15} {why}")

    sendable = [j for j in jobs if (j.get("_touch") or {}).get("mobile") or j["mobile"]]

    if args.send:
        ok_hours, why = within_sending_hours()
        if not ok_hours:
            print(f"\nNot sending: {why}. Messages go out {SEND_HOUR_FROM}:00-"
                  f"{SEND_HOUR_TO}:00 Mon-Fri. Re-run in hours, or set SEND_HOUR_* to override.")
            return

    results: list[tuple[dict, bool, int, str]] = []

    # "auto" exists because the template can be sitting in Meta's review
    # queue when this fires, and a morning where nobody is contacted is
    # worse than a morning contacted by SMS. The decision is made once,
    # from the first send, so the batch does not go out half on each
    # channel and leave a confusing trail on the jobs.
    channel = args.channel
    if channel == "auto":
        channel = "whatsapp"

    for j in sendable:
        link = schedule_link(j["job_uuid"])
        if args.dry_run or not args.send:
            t = j.get("_touch") or {}
            who = f" touch {t['n']} -> {t['to']}" if t else ""
            print(f"\n--- #{j['job_ref']} {j['first']} "
                  f"({t.get('mobile') or j['mobile']}){who} ---")
            if channel == "whatsapp":
                print(f"  template: {WHATSAPP_TEMPLATE}")
                print(f"  params  : {whatsapp_params(j)}")
                print(f"  button  : {link}")
            else:
                print("  " + sms_text(j, link))
            continue

        if channel == "whatsapp":
            status, detail = send_whatsapp(j, link)
            if args.channel == "auto" and status == 409 and "template_not_approved" in detail:
                print("  template still not approved — whole batch falls back to SMS")
                channel = "sms"
                status, detail = send_sms(j, link)
        else:
            status, detail = send_sms(j, link)
        ok = 200 <= status < 300
        print(f"#{j['job_ref']} {j['first']:<14} {channel} HTTP {status} {'' if ok else detail}")
        results.append((j, ok, status, detail))
        if ok:
            rec = state["sent"].setdefault(j["job_uuid"], {"touches": []})
            rec.setdefault("touches", []).append({
                "at": time.time(), "channel": channel,
                "to": (j.get("_touch") or {}).get("to", "occupier"),
            })
            save_state(state)
        # SMS goes straight to ServiceM8 and has no per-minute ceiling;
        # WhatsApp goes through the add-on's limiter and does.
        time.sleep(WHATSAPP_MIN_INTERVAL_SECONDS if channel == "whatsapp" else 0.3)

    if args.notify and results:
        sent = [r for r in results if r[1]]
        failed = [r for r in results if not r[1]]
        lines = [
            f"Booking outreach via {channel}: {len(sent)} sent, {len(failed)} failed"
            + (" (follow-up)" if args.followup else ""),
        ]
        lines += [f"  {j['first']} #{j['job_ref']} {j['service']}" for j, *_ in sent]
        if failed:
            lines.append("FAILED:")
            lines += [f"  {j['first']} #{j['job_ref']} HTTP {st} {d[:60]}"
                      for j, _, st, d in failed]
        if needs_human:
            lines.append(f"{len(needs_human)} need a call from you:")
            lines += [f"  {j['first']} #{j['job_ref']} {why}" for j, why in needs_human]
        if no_mobile:
            lines.append(f"{len(no_mobile)} have no mobile:")
            lines += [f"  {j['first']} #{j['job_ref']} {j['email'] or 'no email'}"
                      for j in no_mobile]
        notify_telegram("\n".join(lines))


if __name__ == "__main__":
    main()
