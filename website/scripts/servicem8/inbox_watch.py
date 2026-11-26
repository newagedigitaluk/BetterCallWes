#!/usr/bin/env python3
"""@mention Wes on every new ServiceM8 Inbox item that would otherwise arrive silently.

ServiceM8 sends no notification for a new Inbox message: its alerts cover
scheduling and staff messages only. ServiceM8 Phone files every call there,
and online enquiries land there too, so they sat unread and never became
jobs. Of the last 50 Inbox items on 26 Nov 2026, 38 were unread, including
14 calls and 2 online enquiries nobody was told about.

What ServiceM8 does notify on is an @mention in a note, so this adds one.
Proven on 27 Sep 2026: the note arrived on Wes's phone, with sound.

Skipped, because something already notifies or nobody needs pinging:
WhatsApps (the ServiceHQ add-on mentions those itself), Google Local
Services leads (lsa_leads.py mentions those), the reviews tool's automatic
notices, and anything already converted to a job or archived.

Notes can't be read back through the API (GET .../notes.json returns the
message), so the record of what's been flagged is our own state file.

    python inbox_watch.py --list       # what it would flag, change nothing
    python inbox_watch.py --backfill   # mark everything current as seen
    python inbox_watch.py --run        # for cron
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ENV = Path("/home/wes/Coding/Projects/Better Call Wes/.env")
STATE = Path(__file__).with_name("inbox-watch-state.json")
API = "https://api.servicem8.com/api_1.0"
MENTION = "@Wesley"
UK = ZoneInfo("Europe/London")
# Don't buzz Wes's phone overnight. Anything that lands outside these hours
# is flagged at the first run after 7am.
QUIET = (22, 7)

SKIP_SUBJECTS = re.compile(
    r"^(WhatsApp from|Google lead|Review link opened|New Google review|Reviews last week|Moved:|ServiceHQ Chat)",
    re.I)


def key() -> str:
    for line in ENV.read_text().splitlines():
        if line.startswith("SERVICEM8_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("SERVICEM8_API_KEY missing from .env")


def sm8(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(
        API + path, method=method, data=json.dumps(body).encode() if body else None,
        headers={"X-Api-Key": key(), "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw.strip() else None


def inbox() -> list[dict]:
    d = sm8("GET", "/inboxmessage.json")
    msgs = d.get("messages", d) if isinstance(d, dict) else d
    return [m for m in msgs if m.get("active") == 1]


def wants_flag(m: dict) -> bool:
    if m.get("converted_to_job_uuid") or str(m.get("is_archived")) in ("1", "true", "True"):
        return False
    if m.get("message_type") in ("phone_call", "online_booking"):
        return True
    return not SKIP_SUBJECTS.match(m.get("subject") or "")


def note_for(m: dict) -> str:
    who = (m.get("from_name") or "unknown").strip()
    text = re.sub(r"\s+", " ", m.get("message_text") or "").strip()
    if m.get("message_type") == "phone_call":
        head = f"Call from {who}"
        # The phone agent writes "Caller: x | Request: y | Details: z | Action: ..."
        req = re.search(r"Request:\s*([^|]+)", text)
        det = re.search(r"Details:\s*([^|]+)", text)
        body = " ".join(p.group(1).strip() for p in (req, det) if p) or text
    elif m.get("message_type") == "online_booking":
        head = f"Online enquiry from {who}"
        desc = re.search(r"Description:\s*(.+)", text)
        body = desc.group(1) if desc else text
    else:
        head = f"{m.get('subject') or 'Message'} from {who}"
        body = text
    body = body.strip() or "no details recorded, ring them back"
    body = body[:220] + ("..." if len(body) > 220 else "")
    return f"{head}: {body} {MENTION}"


def load() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"seen": {}}


def save(s: dict) -> None:
    STATE.write_text(json.dumps(s, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--backfill", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()

    state = load()
    msgs = inbox()

    if a.backfill:
        for m in msgs:
            state["seen"].setdefault(m["uuid"], {"at": time.time(), "flagged": False, "why": "backfill"})
        save(state)
        print(f"marked {len(msgs)} current Inbox items as seen")
        return

    fresh = [m for m in msgs if m["uuid"] not in state["seen"]]
    hour = datetime.now(UK).hour
    quiet = hour >= QUIET[0] or hour < QUIET[1]

    for m in sorted(fresh, key=lambda x: x.get("timestamp", "")):
        if not wants_flag(m):
            if not a.list:
                state["seen"][m["uuid"]] = {"at": time.time(), "flagged": False, "why": "skip"}
            continue
        n = note_for(m)
        if a.list:
            print(f"  {m['timestamp']}  {n}")
            continue
        if quiet:
            continue          # leave unseen; flagged at the first run after 7am
        try:
            sm8("POST", f"/inboxmessage/{m['uuid']}/notes.json", {"note": n})
            state["seen"][m["uuid"]] = {"at": time.time(), "flagged": True}
            print(f"flagged {m['uuid']}: {n[:90]}")
        except urllib.error.HTTPError as e:
            # Not marked seen, so the next run tries again.
            print(f"FAILED {m['uuid']}: {e.code} {e.read()[:150].decode()}")
        save(state)
    if not a.list:
        save(state)


if __name__ == "__main__":
    main()
