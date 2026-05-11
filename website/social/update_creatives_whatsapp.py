"""
Update all 10 BCW ad creatives to use the correct WhatsApp number (447700155655).
Creates new creatives with WHATSAPP_MESSAGE CTA and updates each ad to point to them.
"""

import os, json, requests
from pathlib import Path

TOKEN       = os.environ.get("META_ACCESS_TOKEN", "")
APP_SECRET  = os.environ.get("META_APP_SECRET", "")
BASE_URL    = "https://graph.facebook.com/v19.0"
AD_ACCOUNT  = "act_1157261541704017"
PAGE_ID     = "178728745664355"
WA_NUMBER   = "447700155655"

# The 10 live ads — id: (ad_id, image_hash, name, primary_text, headline, description)
ADS = [
    {
        "ad_id": "120241784398380241",
        "name": "Wes Portrait — Cold Audience",
        "image_hash": "bf172d0c53a90239e0a6c31c58e3e7f5",
        "primary_text": (
            "Southampton's local Gas Safe plumber and heating engineer. "
            "No call centres, no big company markup — just Wes. "
            "WhatsApp me a photo of the problem and I'll tell you what's wrong before I even arrive."
        ),
        "headline": "Boiler Problem? WhatsApp a Photo — I'll Diagnose It First",
        "description": "Gas Safe Registered · Southampton · 07700 155 655",
    },
    {
        "ad_id": "120241784400390241",
        "name": "Heat Exchanger Before/After — Repair Hook",
        "image_hash": "e8ea9e79ee50d670c4d58e4a9da0a977",
        "primary_text": (
            "The heat exchanger on the left came out of a boiler this week. "
            "The owner had no idea their boiler was in this state — it was still working, "
            "but running at half efficiency and heading for a breakdown worth £600+. "
            "An annual boiler service catches this before it costs you."
        ),
        "headline": "This Is What a £600 Breakdown Looks Like Before It Happens",
        "description": "Annual Boiler Service · Better Call Wes · Southampton",
    },
    {
        "ad_id": "120241784401160241",
        "name": "Magnetic Filter Sludge — Shock Hook",
        "image_hash": "b2dcef9d37b041cff191e44dfc707589",
        "primary_text": (
            "This black iron oxide sludge was circulating through a customer's boiler last week. "
            "It coats the heat exchanger, blocks the pump, and silently destroys your boiler from the inside. "
            "A magnetic filter stops it. Most boilers in Southampton don't have one."
        ),
        "headline": "This Sludge Was Silently Destroying Their Boiler",
        "description": "Protects your boiler · Fitted same day · Better Call Wes",
    },
    {
        "ad_id": "120241784402090241",
        "name": "Gutted Old Boiler — Replacement Hook",
        "image_hash": "bc4428ceaf363f6f00f8606939d8eca9",
        "primary_text": (
            "This 16-year-old boiler had been limping along for years, "
            "costing its owner £200–300 a year in repairs. "
            "A new A-rated Worcester boiler pays for itself in energy savings within 4–5 years "
            "— and gives you reliable heating instead of annual breakdown dread."
        ),
        "headline": "Still Paying to Repair a 10-Year-Old Boiler?",
        "description": "Gas Safe Registered · 12-Month Guarantee · Same Day Available",
    },
    {
        "ad_id": "120241784403990241",
        "name": "WhatsApp CTA — Direct Response",
        "image_hash": "ce04ddbb598722ef74cba2d4347e1f1b",
        "primary_text": (
            "Boiler playing up? Radiator cold? Dripping tap driving you mad? "
            "WhatsApp me a photo — I can usually diagnose the problem before I arrive, "
            "which saves time and keeps the cost down. "
            "No call centres. No holding music. Just message Wes directly."
        ),
        "headline": "Cold Radiator? Boiler Playing Up? WhatsApp Me a Photo",
        "description": "Gas Safe Registered · Southampton · Tap to message",
    },
    {
        "ad_id": "120241784404680241",
        "name": "Loft Boiler Install — Premium Showcase",
        "image_hash": "c88897b4b2665e7f264056d7296eb88f",
        "primary_text": (
            "New Worcester boiler fitted in a Southampton loft this week. "
            "Gas Safe registered, all pipework neat, 12-month parts and labour guarantee, "
            "commissioned and running on the same day. "
            "If your boiler is over 10 years old, it's worth getting a quote."
        ),
        "headline": "Same-Day Fit · Gas Safe · 12-Month Guarantee Included",
        "description": "Supply & Fit · Gas Safe · 12-Month Guarantee · Better Call Wes",
    },
    {
        "ad_id": "120241784405730241",
        "name": "What's Included — Trust & Process",
        "image_hash": "a419d3fcfa387e18af8e3c618f9e4820",
        "primary_text": (
            "Every boiler installation we do includes a full system flush, magnetic filter, "
            "and corrosion inhibitor as standard — not as paid extras. "
            "These three things are what separate a boiler that lasts 15 years "
            "from one that breaks down in 3."
        ),
        "headline": "Magnetic Filter + Full Flush — Included, Not an Extra",
        "description": "No hidden extras · Gas Safe Registered · Better Call Wes Southampton",
    },
    {
        "ad_id": "120241784407570241",
        "name": "Smart Boiler — Upgrade Hook",
        "image_hash": "ecf934a549e77bde24c8be1733dbf499",
        "primary_text": (
            "Is your boiler over 10 years old? "
            "New A-rated Worcester boilers can cut your heating bills by up to 30% "
            "compared to an old G-rated unit. "
            "Supply and fit from £2,100, fully Gas Safe registered, 12-month guarantee."
        ),
        "headline": "Cut Heating Bills by Up to 30% — New Boiler From £2,100",
        "description": "Supply & Fit · Gas Safe · Guarantee Included · Better Call Wes",
    },
    {
        "ad_id": "120241784408150241",
        "name": "System Boiler + Cylinder — Upsell",
        "image_hash": "4ab15df233039b6a80f86da0bf78e8af",
        "primary_text": (
            "Tired of cold showers the moment someone else turns a tap on? "
            "A system boiler with an unvented cylinder gives you mains-pressure hot water "
            "to every shower and tap in the house — simultaneously. "
            "No more waiting, no more cold showers."
        ),
        "headline": "No More Cold Showers — Mains Pressure to Every Tap",
        "description": "System Boiler + Cylinder · Southampton · Better Call Wes",
    },
    {
        "ad_id": "120241784414080241",
        "name": "Column Radiator — Aspirational",
        "image_hash": "9843792168833a1e37b37e42c026492c",
        "primary_text": (
            "New cast iron column radiator fitted in a Southampton hallway this week. "
            "If your radiators are tired, corroded, or just not heating the room properly, "
            "we can supply and fit replacements — including designer styles — usually same week. "
            "Message for a quote."
        ),
        "headline": "Radiator Cold, Noisy or Corroded? Same-Week Replacement",
        "description": "Supplied & Fitted · Better Call Wes · Message for a Quote",
    },
]


def api_post(endpoint, payload):
    p = {**payload, "access_token": TOKEN}
    resp = requests.post(f"{BASE_URL}/{endpoint}", data=p, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(json.dumps(data["error"], indent=2))
    return data


def api_post_json(endpoint, payload):
    """POST with JSON body — needed for fields like degrees_of_freedom_spec."""
    params = {"access_token": TOKEN}
    resp = requests.post(f"{BASE_URL}/{endpoint}", params=params, json=payload, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(json.dumps(data["error"], indent=2))
    return data


def extend_token():
    if not APP_SECRET:
        return TOKEN
    resp = requests.get(f"{BASE_URL}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": "1454174139594007",
        "client_secret": APP_SECRET,
        "fb_exchange_token": TOKEN,
    }, timeout=30)
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    return TOKEN


def main():
    global TOKEN
    TOKEN = extend_token()

    print("Updating 10 ad creatives to use WhatsApp number 447700155655...\n")

    for ad in ADS:
        try:
            # Create new creative
            creative = api_post_json(f"{AD_ACCOUNT}/adcreatives", {
                "name": f"Creative — {ad['name']} (v2)",
                "object_story_spec": {
                    "page_id": PAGE_ID,
                    "link_data": {
                        "message": ad["primary_text"],
                        "name": ad["headline"],
                        "description": ad["description"],
                        "image_hash": ad["image_hash"],
                        "link": "https://fb.com/messenger_doc/",
                        "call_to_action": {
                            "type": "MESSAGE_PAGE",
                            "value": {"app_destination": "MESSENGER"},
                        },
                    },
                },
                "degrees_of_freedom_spec": {
                    "creative_features_spec": {
                        "PROFILE_CARD": {"enroll_status": "OPT_OUT"},
                    },
                },
            })
            creative_id = creative["id"]

            # Update the existing ad to use the new creative
            api_post(ad["ad_id"], {
                "creative": json.dumps({"creative_id": creative_id}),
            })

            print(f"  ✅ {ad['name']}")

        except Exception as e:
            print(f"  ❌ {ad['name']} — {e}")

    print("\nDone.")


if __name__ == "__main__":
    if not TOKEN:
        print("Set META_ACCESS_TOKEN in .env")
    else:
        main()
