"""
Facebook/Instagram static ad image generator for Better Call Wes.

Generates ad creatives via Kie AI and saves them locally for upload to Meta Ads Manager.

Usage:
  KIE_API_KEY=... python social/generate_ads.py

Output: website/social/ads/ directory
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
ADS_DIR = PROJECT_ROOT / "social" / "ads"
sys.path.insert(0, str(PROJECT_ROOT / "social"))

ADS_DIR.mkdir(exist_ok=True)

# --- Ad definitions ---
# aspect_ratio: "1:1" (square, universal), "4:5" (portrait, best mobile feed)

ADS = [
    {
        "id": "ad_whatsapp_cta",
        "name": "WhatsApp CTA — Problem list",
        "aspect_ratio": "1:1",
        "prompt": (
            "Create a professional Facebook ad image for a local Gas Safe plumber. "
            "Dark navy blue background (#0F2942). "
            "Bold white heading at top: 'Boiler playing up?'. "
            "Below, three lines in orange (#FF8C00) with red X emojis: "
            "'❌ Strange noises', '❌ Losing pressure', '❌ No hot water'. "
            "Large WhatsApp-green button at bottom with white text: 'WhatsApp a Photo →'. "
            "Small white text below button: 'Gas Safe Registered | Southampton'. "
            "Clean, modern, high contrast. No people. No clutter."
        ),
    },
    {
        "id": "ad_problem_solution",
        "name": "Problem/Solution — Boiler service",
        "aspect_ratio": "4:5",
        "prompt": (
            "Create a professional Facebook ad image for a local boiler engineer. "
            "Split design: top half has a dark navy overlay on a photo-realistic modern boiler, "
            "bottom half is clean white. "
            "Top half bold white text: 'Is your boiler telling you something?'. "
            "Bottom half: three short bullet points in dark navy: "
            "'✓ Upfront quote before any work starts', "
            "'✓ Gas Safe registered engineer', "
            "'✓ 12-month workmanship guarantee'. "
            "Orange CTA button: 'Book a Service →'. "
            "Small text: 'Better Call Wes | Southampton'. "
            "Professional, trustworthy, clean."
        ),
    },
    {
        "id": "ad_trust_credentials",
        "name": "Trust/Credentials — Clean brand ad",
        "aspect_ratio": "1:1",
        "prompt": (
            "Create a clean professional trade services ad. "
            "Navy blue background (#0F2942) with subtle diagonal texture. "
            "Top centre: bold orange text 'BETTER CALL WES'. "
            "Centre: large white headline text 'Southampton's Local Heating & Plumbing Engineer'. "
            "Below headline three white trust icons with labels: "
            "a shield icon 'Gas Safe Registered', a clipboard icon 'Upfront Fixed Quotes', "
            "a star icon '12-Month Guarantee'. "
            "Bottom: orange button 'Get in Touch Today'. "
            "Very clean, premium, no clutter."
        ),
    },
    {
        "id": "ad_landlord",
        "name": "Landlord — Gas Safety Certificate",
        "aspect_ratio": "4:5",
        "prompt": (
            "Create a Facebook ad image targeting landlords. "
            "Clean white background. "
            "Top: bold dark navy text 'Landlords —' with orange accent. "
            "Large headline: 'Gas Safety Certificate Required by Law'. "
            "Middle section with light grey background: "
            "three bullet points in navy: "
            "'✓ CP12 certificate issued same day', "
            "'✓ All gas appliances covered', "
            "'✓ Renewal reminders included'. "
            "Bottom orange CTA button: 'Book Your Check →'. "
            "Small text: 'Gas Safe Registered | Southampton & Surrounding Areas'. "
            "Professional, compliance-focused, trustworthy."
        ),
    },
    {
        "id": "ad_emergency",
        "name": "Emergency — No heating/hot water",
        "aspect_ratio": "1:1",
        "prompt": (
            "Create an urgent Facebook ad image for emergency boiler repair. "
            "Dark background with subtle cold blue tones suggesting winter/cold. "
            "Large bold white text at top: 'No Heating or Hot Water?'. "
            "Below in orange: 'Get it diagnosed and sorted fast.'. "
            "Three short white lines: "
            "'→ Fast response across Southampton', "
            "'→ Upfront quote before work starts', "
            "'→ Gas Safe registered engineer'. "
            "Bright orange CTA button at bottom: 'Call or WhatsApp Now'. "
            "Urgent but professional tone. High contrast."
        ),
    },
]


def upload_to_catbox(file_path: str) -> str:
    """Upload a local file to catbox.moe and return the public URL."""
    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.text.strip()


def download_image(url: str, output_path: Path) -> Path:
    """Download image from URL and save locally."""
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return output_path


def main():
    from kie_client import KieClient

    kie = KieClient()

    credits = kie.check_credits()
    print(f"\n💳 Kie AI credits: {credits}")
    print(f"🖼  Generating {len(ADS)} ad images...\n")

    results = []

    for ad in ADS:
        print(f"{'='*60}")
        print(f"📸 {ad['name']} ({ad['aspect_ratio']})")

        try:
            url = kie.generate_image(
                prompt=ad["prompt"],
                aspect_ratio=ad["aspect_ratio"],
                resolution="2K",
                output_format="jpg",
            )
            print(f"  ✅ Generated: {url[:60]}...")

            # Download locally
            filename = f"{ad['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            local_path = ADS_DIR / filename
            download_image(url, local_path)
            print(f"  💾 Saved: social/ads/{filename}")

            results.append({
                "id": ad["id"],
                "name": ad["name"],
                "aspect_ratio": ad["aspect_ratio"],
                "local_file": str(local_path),
                "kie_url": url,
                "generated_at": datetime.now().isoformat(),
            })

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            results.append({
                "id": ad["id"],
                "name": ad["name"],
                "error": str(e),
            })

        print()

    # Save manifest
    manifest_path = ADS_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)

    credits_after = kie.check_credits()
    print(f"{'='*60}")
    print(f"\n✅ Done. {len([r for r in results if 'local_file' in r])}/{len(ADS)} generated.")
    print(f"📁 Files saved to: website/social/ads/")
    print(f"💳 Credits used: {credits - credits_after} | Remaining: {credits_after}")
    print(f"\nUpload the images from website/social/ads/ directly to Meta Ads Manager.")


if __name__ == "__main__":
    main()
