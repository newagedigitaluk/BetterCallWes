#!/usr/bin/env python3
"""Google Local Services leads: alert Wes, and open a WhatsApp conversation.

Google charges per lead and ranks partly on how fast you respond, so the
window that matters is minutes, not hours. The lead notification emails are
no use for automation: they carry the message but not the phone number, on
purpose. The Google Ads API carries both, which is why this reads the API
instead of the mailbox.

Two kinds of lead, handled differently:

  MESSAGE     someone typed an enquiry. We can answer it, so a WhatsApp
              template goes out opening a conversation, and their reply
              lands in the ServiceHQ add-on where Wes can talk freely.
  PHONE_CALL  they rang. Wes has either spoken to them or missed them, and
              an automatic text either way reads as nobody paying attention.
              Telegram only.

Deliberately does NOT create a ServiceM8 job. Most enquiries never convert,
and a job plus a company record for each one would leave the work list full
of dead ends. Revisit once there is a feel for the conversion rate.

    python lsa_leads.py --list          # what's there, send nothing
    python lsa_leads.py --dry-run       # render the messages
    python lsa_leads.py --send          # for cron

Env: GOOGLE_ADS_CLIENT_ID / _CLIENT_SECRET / _REFRESH_TOKEN, SERVICEHQ_KEY.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

CUSTOMER_ID = os.environ.get("LSA_CUSTOMER_ID", "3558748555")
API = "https://googleads.googleapis.com/v23"
STATE = Path(__file__).with_name("lsa-state.json")

SERVICEHQ_SEND_URL = os.environ.get(
    "SERVICEHQ_SEND_URL", "https://wa.servicehq.co.uk/api/service/send-template")
SERVICEHQ_KEY = os.environ.get("SERVICEHQ_KEY", "")
TEMPLATE = os.environ.get("LSA_TEMPLATE", "lsa_lead_first_reply")
TEMPLATE_LANG = os.environ.get("LSA_TEMPLATE_LANG", "en_GB")

# Google's own service ids, as they come back on the lead. Anything not
# listed falls back to the category, then to "a plumbing job".
SERVICE_LABEL = {
    "service_boiler": "a boiler service",
    "repair_water_heater": "a water heater repair",
    "repair_hot_water_cylinder": "a hot water cylinder repair",
    "install_hot_water_cylinder": "a new hot water cylinder",
    "repair_faucet": "a tap repair",
    "repair_pipe": "a pipe repair",
    "install_toilet": "a toilet installation",
    "install_shower": "a shower installation",
}
CATEGORY_LABEL = {
    "xcat:service_area_business_hvac": "your boiler or heating",
    "xcat:service_area_business_plumber": "a plumbing job",
}

# Prices come from the materials list in ServiceM8, not from thin air:
# LAB-BOIL-STAN is £100 and the online form adds the CP12 at £50, which is
# what job 4672 was actually billed. Quoting anything else here would mean
# the first message disagrees with the booking page.
PRICE_LINE = {
    "service_boiler": ("A standard boiler service is £100, or £150 done together "
                       "with a gas safety certificate."),
}
PRICE_FALLBACK = ("I'd need a couple more details to price that properly, but I'll "
                  "give you a straight answer once I know what's involved.")


# ─────────────────────────── Google Ads ───────────────────────────

def access_token() -> str:
    body = urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def query(tok: str, sql: str) -> list[dict]:
    req = urllib.request.Request(
        f"{API}/customers/{CUSTOMER_ID}/googleAds:search",
        data=json.dumps({"query": sql}).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r).get("results", [])


def fetch_leads(tok: str, limit: int = 25) -> list[dict]:
    """Recent leads, newest first, with the customer's own words attached.

    contact_details has to be selected whole. Its sub-fields are documented
    but not individually selectable, and asking for
    contact_details.phone_number comes back UNRECOGNIZED_FIELD.
    """
    leads = query(tok,
        "SELECT local_services_lead.id, local_services_lead.lead_type, "
        "local_services_lead.lead_status, local_services_lead.lead_charged, "
        "local_services_lead.category_id, local_services_lead.service_id, "
        "local_services_lead.creation_date_time, local_services_lead.contact_details "
        f"FROM local_services_lead ORDER BY local_services_lead.creation_date_time DESC "
        f"LIMIT {limit}")
    convos: dict[str, list[str]] = {}
    for row in query(tok,
        "SELECT local_services_lead_conversation.lead, "
        "local_services_lead_conversation.participant_type, "
        "local_services_lead_conversation.message_details.text "
        "FROM local_services_lead_conversation "
        f"ORDER BY local_services_lead_conversation.event_date_time DESC LIMIT {limit * 3}"):
        c = row["localServicesLeadConversation"]
        text = (c.get("messageDetails") or {}).get("text")
        if text and c.get("participantType") == "CONSUMER":
            convos.setdefault(c["lead"].split("/")[-1], []).append(text)

    out = []
    for row in leads:
        l = row["localServicesLead"]
        cd = l.get("contactDetails") or {}
        svc = l.get("serviceId")
        out.append({
            "id": l["id"],
            "type": l.get("leadType"),
            "status": l.get("leadStatus"),
            "charged": bool(l.get("leadCharged")),
            "service": svc,
            "category": l.get("categoryId"),
            "created": l.get("creationDateTime", "")[:16],
            "phone": cd.get("phoneNumber"),
            "email": cd.get("email"),
            "name": cd.get("consumerName"),
            "message": " ".join(convos.get(l["id"], [])).strip(),
            "label": SERVICE_LABEL.get(svc) or CATEGORY_LABEL.get(l.get("categoryId"))
                     or "a plumbing job",
            "price": PRICE_LINE.get(svc, PRICE_FALLBACK),
        })
    return out


# ─────────────────────────── Sending ───────────────────────────

def send_whatsapp(lead: dict) -> tuple[int, str]:
    if not SERVICEHQ_KEY:
        return 0, "SERVICEHQ_KEY not set"
    payload = {
        "to": lead["phone"],
        "template": TEMPLATE,
        "language": TEMPLATE_LANG,
        "bodyParams": [lead["label"], lead["price"]],
        "preview": preview(lead),
    }
    req = urllib.request.Request(
        SERVICEHQ_SEND_URL, method="POST", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {SERVICEHQ_KEY}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read()[:200].decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:250].decode()
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:150]


def preview(lead: dict) -> str:
    return (f"Hi, this is Wes from Better Call Wes. You enquired through Google about "
            f"{lead['label']}, and I'm the Gas Safe engineer who picked it up.\n\n"
            f"{lead['price']}\n\nWhereabouts are you, and when were you hoping to "
            f"get it done?")


def notify(text: str) -> bool:
    """Telegram, best effort. Kept local rather than imported from the booking
    API so a lead alert can never be taken out by an unrelated import."""
    try:
        base = Path.home() / ".claude" / "channels" / "telegram-bcw"
        token = next((ln.split("=", 1)[1].strip()
                      for ln in (base / ".env").read_text().splitlines()
                      if ln.startswith("TELEGRAM_BOT_TOKEN=")), None)
        chat = json.loads((base / "access.json").read_text())["allowFrom"][0]
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=json.dumps({"chat_id": chat, "text": text,
                             "disable_web_page_preview": True}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:  # noqa: BLE001
        print(f"  (telegram failed: {e})")
        return False


def alert_text(lead: dict, wa: str) -> str:
    bits = [f"New Google lead - {lead['type'].replace('_', ' ').lower()}",
            f"{lead['label']}" + (f" - {lead['name']}" if lead["name"] else ""),
            f"{lead['phone'] or 'no number'}" + (f"  {lead['email']}" if lead["email"] else "")]
    if lead["message"]:
        bits += ["", lead["message"][:600]]
    bits += ["", wa,
             f"https://ads.google.com/localservices/lead?lid={lead['id']}"]
    if lead["charged"]:
        bits.append("(charged)")
    return "\n".join(bits)


# ─────────────────────────── Main ───────────────────────────

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"done": {}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    leads = fetch_leads(access_token(), args.limit)
    state = load_state()

    if args.list:
        for l in leads:
            seen = "done" if l["id"] in state["done"] else "NEW"
            print(f"  {l['created']}  {l['type']:<10} {l['status']:<9} {seen:<4} "
                  f"{l['phone'] or '(none)':<15} {l['label']:<28} {l['message'][:50]}")
        return

    fresh = [l for l in leads if l["id"] not in state["done"]]
    print(f"{len(fresh)} new of {len(leads)} leads")

    for l in fresh:
        # A call lead gets a nudge, never a message. See the module docstring.
        wa = "phone lead - ring them back" if l["type"] == "PHONE_CALL" else (
             "no mobile on the lead" if not l["phone"] else "WhatsApp sent")

        if args.dry_run or not args.send:
            print(f"\n--- {l['id']}  {l['type']}  {l['phone']} ---")
            print("  " + preview(l).replace("\n", "\n  ") if l["type"] == "MESSAGE"
                  and l["phone"] else f"  ({wa})")
            continue

        if l["type"] == "MESSAGE" and l["phone"]:
            status, detail = send_whatsapp(l)
            ok = 200 <= status < 300
            wa = "WhatsApp sent" if ok else f"WhatsApp FAILED {status} {detail[:120]}"
            print(f"  {l['id']} {wa}")
            time.sleep(13)          # add-on allows 5/min and counts failures
        notify(alert_text(l, wa))
        state["done"][l["id"]] = {"at": time.time(), "type": l["type"], "wa": wa}
        STATE.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
