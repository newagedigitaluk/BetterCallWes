"""
Meta Ads Campaign Creator — Better Call Wes

Creates the full ad campaign via Meta Marketing API:
  - 1 campaign (CBO, starts PAUSED so you can review before going live)
  - Ad Set 1: Cold audience — Southampton, age 30-65
  - Ad Set 2: Warm audience — Southampton, age 35-65, home improvement interest
  - 10 ads with images uploaded and copy pre-loaded

Required env vars:
  META_ACCESS_TOKEN  — from Graph API Explorer
  META_APP_SECRET    — from developers.facebook.com app settings (for 60-day token)

Usage:
  META_ACCESS_TOKEN=... META_APP_SECRET=... python website/social/create_meta_ads.py

The campaign is created as PAUSED. Review in Ads Manager then set to ACTIVE.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Credentials & constants
# ---------------------------------------------------------------------------
ACCESS_TOKEN   = os.environ.get("META_ACCESS_TOKEN", "")
APP_SECRET     = os.environ.get("META_APP_SECRET", "")
APP_ID         = "1454174139594007"
AD_ACCOUNT_ID  = "act_1157261541704017"
PAGE_ID        = "178728745664355"
WHATSAPP_NUM   = "447700155655"

BASE_URL   = "https://graph.facebook.com/v19.0"
ADS_DIR    = Path(__file__).parent / "ads" / "v2"

CAMPAIGN_NAME     = "BCW — Messenger Leads — v2"
DAILY_BUDGET_GBP  = 10.00   # £10/day — change here to adjust spend
DAILY_BUDGET_PENCE = int(DAILY_BUDGET_GBP * 100)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def api_get(endpoint: str, params: dict = None) -> dict:
    p = params or {}
    p["access_token"] = ACCESS_TOKEN
    resp = requests.get(f"{BASE_URL}/{endpoint}", params=p, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"GET /{endpoint} → {data['error']['message']}")
    return data


def api_post(endpoint: str, payload: dict = None, files: dict = None) -> dict:
    p = payload or {}
    p["access_token"] = ACCESS_TOKEN
    if files:
        resp = requests.post(f"{BASE_URL}/{endpoint}", data=p, files=files, timeout=60)
    else:
        resp = requests.post(f"{BASE_URL}/{endpoint}", data=p, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"POST /{endpoint} → {json.dumps(data['error'], indent=2)}")
    return data


# ---------------------------------------------------------------------------
# Token extension (short-lived → 60-day)
# ---------------------------------------------------------------------------
def extend_token() -> str:
    """Exchange short-lived token for a 60-day long-lived token."""
    if not APP_SECRET:
        print("  ⚠️  META_APP_SECRET not set — skipping token extension.")
        print("     Token will expire in ~1 hour.")
        return ACCESS_TOKEN

    print("🔄 Extending token to 60 days...")
    resp = requests.get(f"{BASE_URL}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": ACCESS_TOKEN,
    }, timeout=30)
    data = resp.json()
    if "error" in data:
        print(f"  ⚠️  Token extension failed: {data['error']['message']}")
        return ACCESS_TOKEN

    long_token = data["access_token"]
    expires_in = data.get("expires_in", "unknown")
    print(f"  ✅ Long-lived token obtained (expires in {expires_in}s / ~60 days)")
    print(f"\n  💾 Save this for next time:\n  META_ACCESS_TOKEN={long_token}\n")
    return long_token


# ---------------------------------------------------------------------------
# Step 1: Verify token
# ---------------------------------------------------------------------------
def verify_token():
    print("🔑 Verifying access token...")
    data = api_get("me", {"fields": "name,id"})
    print(f"  ✅ Authenticated as: {data['name']} (ID: {data['id']})")


# ---------------------------------------------------------------------------
# Step 2: Upload images
# ---------------------------------------------------------------------------
def upload_images(image_files: list[Path]) -> dict[str, str]:
    """Upload images to ad account. Returns {filename_stem: image_hash}."""
    print(f"\n📤 Uploading {len(image_files)} images to ad account...")
    hashes = {}
    for img_path in image_files:
        if not img_path.exists():
            print(f"  ⚠️  Not found — skipping: {img_path.name}")
            continue
        with open(img_path, "rb") as f:
            data = api_post(
                f"{AD_ACCOUNT_ID}/adimages",
                payload={"name": img_path.name},
                files={img_path.name: f},
            )
        images = data.get("images", {})
        for _filename, info in images.items():
            h = info.get("hash")
            hashes[img_path.stem] = h
            print(f"  ✅ {img_path.name} → {h}")
    return hashes


# ---------------------------------------------------------------------------
# Step 3: Create campaign
# ---------------------------------------------------------------------------
def create_campaign() -> str:
    print(f"\n📢 Creating campaign: {CAMPAIGN_NAME}")
    data = api_post(f"{AD_ACCOUNT_ID}/campaigns", {
        "name": CAMPAIGN_NAME,
        "objective": "OUTCOME_ENGAGEMENT",
        "status": "PAUSED",
        "special_ad_categories": json.dumps([]),
        "is_adset_budget_sharing_enabled": "false",
    })
    campaign_id = data["id"]
    print(f"  ✅ Campaign created: {campaign_id}")
    return campaign_id


# ---------------------------------------------------------------------------
# Step 4: Create ad sets
# ---------------------------------------------------------------------------
# Southampton city centre coordinates
SOUTHAMPTON = {
    "latitude": 50.9097,
    "longitude": -1.4044,
    "radius": 10,
    "distance_unit": "mile",
}

def create_ad_set(campaign_id: str, name: str, targeting: dict) -> str:
    print(f"\n🎯 Creating ad set: {name}")
    data = api_post(f"{AD_ACCOUNT_ID}/adsets", {
        "name": name,
        "campaign_id": campaign_id,
        "status": "PAUSED",
        "optimization_goal": "CONVERSATIONS",
        "billing_event": "IMPRESSIONS",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "daily_budget": DAILY_BUDGET_PENCE,
        "destination_type": "MESSENGER",
        "targeting": json.dumps(targeting),
        "promoted_object": json.dumps({"page_id": PAGE_ID}),
    })
    ad_set_id = data["id"]
    print(f"  ✅ Ad set created: {ad_set_id}")
    return ad_set_id


COLD_TARGETING = {
    "age_min": 18,
    "age_max": 65,
    "geo_locations": {
        "custom_locations": [SOUTHAMPTON],
    },
}

WARM_TARGETING = {
    "age_min": 18,
    "age_max": 65,
    "geo_locations": {
        "custom_locations": [SOUTHAMPTON],
    },
    "flexible_spec": [{
        "interests": [
            {"id": "6003397425735", "name": "Home improvement"},
        ],
    }],
}


# ---------------------------------------------------------------------------
# Step 5: Ad definitions (image + copy)
# ---------------------------------------------------------------------------
ADS = [
    # --- Cold ad set (4 ads) ---
    {
        "ad_set": "cold",
        "id": "face_smile",
        "name": "Wes Portrait — Cold Audience",
        "image_stem": "v2_face_smile_20260324_111256",
        "primary_text": (
            "Southampton's local Gas Safe plumber and heating engineer. "
            "No call centres, no big company markup — just Wes. "
            "WhatsApp me a photo of the problem and I'll tell you what's wrong before I even arrive."
        ),
        "headline": "Better Call Wes — Local Plumbing & Heating",
        "description": "Gas Safe Registered · Southampton · 07700 155 655",
    },
    {
        "ad_set": "cold",
        "id": "before_after_heatex",
        "name": "Heat Exchanger Before/After — Repair Hook",
        "image_stem": "v2_before_after_heatex_20260324_111527",
        "primary_text": (
            "The heat exchanger on the left came out of a boiler this week. "
            "The owner had no idea their boiler was in this state — it was still working, "
            "but running at half efficiency and heading for a breakdown worth £600+. "
            "An annual boiler service catches this before it costs you."
        ),
        "headline": "Is Your Boiler Hiding This?",
        "description": "Annual Boiler Service · Better Call Wes · Southampton",
    },
    {
        "ad_set": "cold",
        "id": "magnetic_filter_sludge",
        "name": "Magnetic Filter Sludge — Shock Hook",
        "image_stem": "v2_magnetic_filter_sludge_20260324_192812",
        "primary_text": (
            "This black iron oxide sludge was circulating through a customer's boiler last week. "
            "It coats the heat exchanger, blocks the pump, and silently destroys your boiler from the inside. "
            "A magnetic filter stops it. Most boilers in Southampton don't have one."
        ),
        "headline": "Magnetic Filter Fitted From £150",
        "description": "Protects your boiler · Fitted same day · Better Call Wes",
    },
    {
        "ad_set": "cold",
        "id": "old_boiler_stripped",
        "name": "Gutted Old Boiler — Replacement Hook",
        "image_stem": "v2_old_boiler_stripped_20260324_112105",
        "primary_text": (
            "This 16-year-old boiler had been limping along for years, "
            "costing its owner £200–300 a year in repairs. "
            "A new A-rated Worcester boiler pays for itself in energy savings within 4–5 years "
            "— and gives you reliable heating instead of annual breakdown dread."
        ),
        "headline": "New Boiler From £2,100 — Supply & Fit",
        "description": "Gas Safe Registered · 12-Month Guarantee · Same Day Available",
    },
    # --- Warm ad set (6 ads) ---
    {
        "ad_set": "warm",
        "id": "face_whatsapp",
        "name": "WhatsApp CTA — Direct Response",
        "image_stem": "v2_face_whatsapp_20260324_111357",
        "primary_text": (
            "Boiler playing up? Radiator cold? Dripping tap driving you mad? "
            "WhatsApp me a photo — I can usually diagnose the problem before I arrive, "
            "which saves time and keeps the cost down. "
            "No call centres. No holding music. Just message Wes directly."
        ),
        "headline": "WhatsApp Wes — Get a Same-Day Answer",
        "description": "Gas Safe Registered · Southampton · Tap to message",
    },
    {
        "ad_set": "warm",
        "id": "loft_install",
        "name": "Loft Boiler Install — Premium Showcase",
        "image_stem": "v2_loft_install_20260324_111607",
        "primary_text": (
            "New Worcester boiler fitted in a Southampton loft this week. "
            "Gas Safe registered, all pipework neat, 12-month parts and labour guarantee, "
            "commissioned and running on the same day. "
            "If your boiler is over 10 years old, it's worth getting a quote."
        ),
        "headline": "New Boiler Fitted From £2,100",
        "description": "Supply & Fit · Gas Safe · 12-Month Guarantee · Better Call Wes",
    },
    {
        "ad_set": "warm",
        "id": "corrosion_inhibitor",
        "name": "What's Included — Trust & Process",
        "image_stem": "v2_corrosion_inhibitor_20260324_112241",
        "primary_text": (
            "Every boiler installation we do includes a full system flush, magnetic filter, "
            "and corrosion inhibitor as standard — not as paid extras. "
            "These three things are what separate a boiler that lasts 15 years "
            "from one that breaks down in 3."
        ),
        "headline": "This Is Included as Standard",
        "description": "No hidden extras · Gas Safe Registered · Better Call Wes Southampton",
    },
    {
        "ad_set": "warm",
        "id": "smart_boiler",
        "name": "Smart Boiler — Upgrade Hook",
        "image_stem": "v2_smart_boiler_20260324_165156",
        "primary_text": (
            "Is your boiler over 10 years old? "
            "New A-rated Worcester boilers can cut your heating bills by up to 30% "
            "compared to an old G-rated unit. "
            "Supply and fit from £2,100, fully Gas Safe registered, 12-month guarantee."
        ),
        "headline": "New Boiler From £2,100 — Fitted Today",
        "description": "Supply & Fit · Gas Safe · Guarantee Included · Better Call Wes",
    },
    {
        "ad_set": "warm",
        "id": "system_install_cylinder",
        "name": "System Boiler + Cylinder — Upsell",
        "image_stem": "v2_system_install_cylinder_20260324_112421",
        "primary_text": (
            "Tired of cold showers the moment someone else turns a tap on? "
            "A system boiler with an unvented cylinder gives you mains-pressure hot water "
            "to every shower and tap in the house — simultaneously. "
            "No more waiting, no more cold showers."
        ),
        "headline": "Unlimited Hot Water · Mains Pressure to Every Tap",
        "description": "System Boiler + Cylinder · Southampton · Better Call Wes",
    },
    {
        "ad_set": "warm",
        "id": "column_radiator",
        "name": "Column Radiator — Aspirational",
        "image_stem": "v2_column_radiator_20260324_165236",
        "primary_text": (
            "New cast iron column radiator fitted in a Southampton hallway this week. "
            "If your radiators are tired, corroded, or just not heating the room properly, "
            "we can supply and fit replacements — including designer styles — usually same week. "
            "Message for a quote."
        ),
        "headline": "New Radiator Fitted — Southampton",
        "description": "Supplied & Fitted · Better Call Wes · Message for a Quote",
    },
]


# ---------------------------------------------------------------------------
# Step 6: Create ad creative
# ---------------------------------------------------------------------------
def create_ad_creative(ad: dict, image_hash: str) -> str:
    data = api_post(f"{AD_ACCOUNT_ID}/adcreatives", {
        "name": f"Creative — {ad['name']}",
        "object_story_spec": json.dumps({
            "page_id": PAGE_ID,
            "link_data": {
                "message": ad["primary_text"],
                "name": ad["headline"],
                "description": ad["description"],
                "image_hash": image_hash,
                "link": f"https://www.facebook.com/{PAGE_ID}",
                "call_to_action": {
                    "type": "MESSAGE_PAGE",
                },
            },
        }),
    })
    return data["id"]


# ---------------------------------------------------------------------------
# Step 7: Create ad
# ---------------------------------------------------------------------------
def create_ad(name: str, ad_set_id: str, creative_id: str) -> str:
    data = api_post(f"{AD_ACCOUNT_ID}/ads", {
        "name": name,
        "adset_id": ad_set_id,
        "creative": json.dumps({"creative_id": creative_id}),
        "status": "PAUSED",
    })
    return data["id"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global ACCESS_TOKEN

    if not ACCESS_TOKEN:
        print("❌ META_ACCESS_TOKEN not set. Run:")
        print("   META_ACCESS_TOKEN=... python website/social/create_meta_ads.py")
        sys.exit(1)

    print("=" * 60)
    print("Better Call Wes — Meta Ads Campaign Creator")
    print("=" * 60)

    # Extend token if App Secret available
    ACCESS_TOKEN = extend_token()

    # Verify
    verify_token()

    # Use pre-uploaded image hashes if available (skip re-upload)
    CACHED_HASHES = {
        "v2_face_smile_20260324_111256":         "bf172d0c53a90239e0a6c31c58e3e7f5",
        "v2_before_after_heatex_20260324_111527": "e8ea9e79ee50d670c4d58e4a9da0a977",
        "v2_magnetic_filter_sludge_20260324_192812": "b2dcef9d37b041cff191e44dfc707589",
        "v2_old_boiler_stripped_20260324_112105": "bc4428ceaf363f6f00f8606939d8eca9",
        "v2_face_whatsapp_20260324_111357":       "ce04ddbb598722ef74cba2d4347e1f1b",
        "v2_loft_install_20260324_111607":        "c88897b4b2665e7f264056d7296eb88f",
        "v2_corrosion_inhibitor_20260324_112241": "a419d3fcfa387e18af8e3c618f9e4820",
        "v2_smart_boiler_20260324_165156":        "ecf934a549e77bde24c8be1733dbf499",
        "v2_system_install_cylinder_20260324_112421": "4ab15df233039b6a80f86da0bf78e8af",
        "v2_column_radiator_20260324_165236":     "9843792168833a1e37b37e42c026492c",
    }
    print(f"\n📤 Using {len(CACHED_HASHES)} pre-uploaded image hashes (skipping re-upload)")
    image_hashes = CACHED_HASHES

    missing = [ad["id"] for ad in ADS if ad["image_stem"] not in image_hashes]
    if missing:
        print(f"\n⚠️  Missing image hashes for: {missing}")
        print("   These ads will be skipped.")

    # Create campaign (skip if already created)
    existing_campaign_id = os.environ.get("META_CAMPAIGN_ID", "")
    if existing_campaign_id:
        campaign_id = existing_campaign_id
        print(f"\n📢 Using existing campaign: {campaign_id}")
    else:
        campaign_id = create_campaign()

    # Create ad sets (skip if already created)
    existing_cold_id = os.environ.get("META_COLD_SET_ID", "")
    existing_warm_id = os.environ.get("META_WARM_SET_ID", "")
    if existing_cold_id and existing_warm_id:
        cold_set_id = existing_cold_id
        warm_set_id = existing_warm_id
        print(f"\n🎯 Using existing ad sets: Cold={cold_set_id} Warm={warm_set_id}")
    else:
        cold_set_id = create_ad_set(campaign_id, "Cold — Southampton 30-65", COLD_TARGETING)
        warm_set_id = create_ad_set(campaign_id, "Warm — Southampton Home Improvement", WARM_TARGETING)

    ad_set_map = {"cold": cold_set_id, "warm": warm_set_id}

    # Create ads
    print(f"\n🖼  Creating {len(ADS)} ads...")
    results = []
    for ad in ADS:
        image_hash = image_hashes.get(ad["image_stem"])
        if not image_hash:
            print(f"  ⚠️  Skipping {ad['name']} — no image hash")
            continue
        try:
            creative_id = create_ad_creative(ad, image_hash)
            ad_set_id = ad_set_map[ad["ad_set"]]
            ad_id = create_ad(ad["name"], ad_set_id, creative_id)
            print(f"  ✅ {ad['name']} — ad ID: {ad_id}")
            results.append({"id": ad["id"], "ad_id": ad_id, "creative_id": creative_id, "status": "created"})
        except Exception as e:
            print(f"  ❌ {ad['name']} — {e}")
            results.append({"id": ad["id"], "status": "failed", "error": str(e)})

    # Summary
    success = len([r for r in results if r["status"] == "created"])
    print(f"\n{'=' * 60}")
    print(f"✅ Done. {success}/{len(ADS)} ads created.")
    print(f"\n📋 Campaign ID: {campaign_id}")
    print(f"   Cold ad set: {cold_set_id}")
    print(f"   Warm ad set: {warm_set_id}")
    print(f"\n🔗 Review in Ads Manager:")
    print(f"   https://www.facebook.com/adsmanager/manage/campaigns?act={AD_ACCOUNT_ID.replace('act_', '')}")
    print(f"\n⚠️  Everything is PAUSED. Set campaign to ACTIVE in Ads Manager when ready to spend.")

    # Save result log
    log_path = ADS_DIR / f"meta_ads_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({
            "campaign_id": campaign_id,
            "cold_ad_set_id": cold_set_id,
            "warm_ad_set_id": warm_set_id,
            "ads": results,
            "created_at": datetime.now().isoformat(),
        }, f, indent=2)
    print(f"\n💾 Log saved: {log_path.name}")


if __name__ == "__main__":
    main()
