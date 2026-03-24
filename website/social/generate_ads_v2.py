"""
Ad creative generator v2 — Better Call Wes.

Uses real brand/work photos as base images (image-to-image via Kie AI).
Adds minimal branded overlays only — keeps the authentic photo feel.

Current Meta best practice for local trades:
- Real photos vastly outperform designed AI graphics for cold audiences
- Face-on-camera is the single highest-performing format
- Minimal text overlay preserves authenticity
- Before/after pairs drive strong engagement

Usage:
  KIE_API_KEY=... python social/generate_ads_v2.py

Output: website/social/ads/v2/
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
ADS_DIR = PROJECT_ROOT / "social" / "ads" / "v2"
BRAND_IMAGES = PROJECT_ROOT / "Brand Images"
WORK_IMAGES = PROJECT_ROOT / "Brand Images" / "Work Images"

sys.path.insert(0, str(PROJECT_ROOT / "social"))

ADS_DIR.mkdir(parents=True, exist_ok=True)


def upload_to_catbox(file_path: str) -> str:
    """Upload a local image to catbox.moe and return the public URL."""
    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload", "userhash": ""},
            files={"fileToUpload": f},
            timeout=60,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"catbox upload failed: {url}")
    return url


def download_image(url: str, output_path: Path) -> Path:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return output_path


# ---------------------------------------------------------------------------
# Ad definitions — all using real photos as base
# Prompt strategy: keep the photo authentic, add ONLY a slim bottom banner
# ---------------------------------------------------------------------------

ADS = [
    {
        "id": "face_smile",
        "name": "Face — Wes smiling in garden (cold audience)",
        "aspect_ratio": "4:5",
        "base_image": str(BRAND_IMAGES / "IMG_1244.JPG"),
        "prompt": (
            "Keep this photo completely unchanged — do not alter the person, colours, background, or composition. "
            "Add ONLY a slim semi-transparent dark navy (#0A2540) banner strip at the very bottom of the image "
            "(about 15% height). Inside the banner, add: "
            "bold white text 'Better Call Wes' on the left, "
            "smaller white text 'Plumbing & Heating · Southampton' below it, "
            "and a small orange circle badge on the right with white text 'Gas Safe'. "
            "The banner must be subtle — the photo fills the frame. No other changes."
        ),
    },
    {
        "id": "face_whatsapp",
        "name": "Face — WhatsApp CTA (Wes with phone)",
        "aspect_ratio": "4:5",
        "base_image": str(BRAND_IMAGES / "IMG_1257.JPG"),
        "prompt": (
            "Keep this photo of the engineer completely unchanged. "
            "Add a clean white speech-bubble style caption box at the top of the image: "
            "bold dark navy text 'Boiler playing up?' on the first line, "
            "then 'WhatsApp me a photo — I diagnose it before I arrive.' "
            "At the very bottom, add a slim dark navy banner: "
            "white text 'Better Call Wes · 07700 155 655' and a small green WhatsApp icon. "
            "Keep 80% of the photo clearly visible. Natural, authentic feel."
        ),
    },
    {
        "id": "before_after_heatex",
        "name": "Before/After — Baxi heat exchangers (repair hook)",
        "aspect_ratio": "1:1",
        "base_image": str(WORK_IMAGES / "IMG_1902.jpg"),
        "prompt": (
            "Keep this photo unchanged — it shows two boiler heat exchangers side by side, one clean and one heavily fouled. "
            "Add a bold white label 'BEFORE' with a red background box over the dirty one on the right, "
            "and 'AFTER' with a green background box over the clean one on the left. "
            "At the top, add a dark navy semi-transparent banner strip: "
            "bold white text 'Is this hiding inside YOUR boiler?' "
            "At the bottom, slim navy banner: white text 'Better Call Wes · Boiler Repair · Southampton'. "
            "Keep the photo as the hero — labels only, no other changes."
        ),
    },
    {
        "id": "loft_install",
        "name": "Boiler install — loft with exposed brick (showcase)",
        "aspect_ratio": "4:5",
        "base_image": str(WORK_IMAGES / "IMG_1926.jpg"),
        "prompt": (
            "Keep this photo of a new Worcester boiler installed in a loft with exposed brick wall unchanged. "
            "Add ONLY a slim semi-transparent dark navy banner at the very bottom: "
            "bold white text 'New Boiler Fitted · Same Day · Southampton', "
            "and below that smaller white text 'Gas Safe Registered · 12-Month Guarantee'. "
            "Small orange accent line above the banner text. "
            "No other modifications. The authentic installation photo must dominate."
        ),
    },
    {
        "id": "smart_boiler",
        "name": "Smart boiler — Worcester CDi circular display (upgrade hook)",
        "aspect_ratio": "1:1",
        "base_image": str(WORK_IMAGES / "IMG_4813.jpg"),
        "prompt": (
            "This photo shows a modern Worcester boiler with a circular smart display. "
            "First, remove the black folder with 'NewAge Boiler Installations' text sitting at the base of the boiler — "
            "replace it cleanly with the floor/background tile material so it looks like it was never there. "
            "Keep everything else in the photo completely unchanged. "
            "Then add a clean white rounded-corner tag in the top-right corner: "
            "bold dark navy text 'New Boiler' on top, orange text 'From £2,100' below. "
            "At the bottom, add a slim dark navy banner: "
            "white text 'Supply & Fit · Gas Safe · Better Call Wes'. "
            "The sleek modern boiler must remain the hero of the image."
        ),
    },
    {
        "id": "column_radiator",
        "name": "Aspirational — cast iron column radiator",
        "aspect_ratio": "4:5",
        "base_image": str(WORK_IMAGES / "IMG_0704.JPG"),
        "prompt": (
            "Keep this photo of a dark grey cast iron column radiator in a hallway completely unchanged. "
            "Add a slim semi-transparent dark navy banner at the very bottom of the image: "
            "bold white text 'New Radiator Fitted Today', "
            "smaller white text below 'Southampton & Surrounding Areas · Better Call Wes'. "
            "Keep the radiator and room as the hero. Nothing else added."
        ),
    },
    {
        "id": "old_boiler_stripped",
        "name": "Before — gutted old boiler (replacement hook)",
        "aspect_ratio": "1:1",
        "base_image": str(WORK_IMAGES / "IMG_4990.jpg"),
        "prompt": (
            "Keep this photo of a completely stripped and gutted old boiler on a wall unchanged. "
            "Add a bold semi-transparent dark overlay banner at the TOP of the image: "
            "large white text 'Sound familiar?' "
            "At the bottom, a solid dark navy banner: "
            "bold orange text 'New Boiler From £2,100', "
            "smaller white text 'Supply & Fit · Same Day · Gas Safe Registered'. "
            "The shocking before-state photo must stay dominant and visible."
        ),
    },
    {
        "id": "corrosion_inhibitor",
        "name": "Trust/process — corrosion inhibitor action shot",
        "aspect_ratio": "1:1",
        "base_image": str(WORK_IMAGES / "IMG_1851.JPG"),
        "prompt": (
            "Keep this action photo of corrosion inhibitor being poured into a magnetic filter completely unchanged. "
            "Add a white semi-transparent rounded caption box overlaid at the top: "
            "bold dark navy text 'Every installation includes:' "
            "then three short lines in dark navy: '✓ Magnetic system filter' '✓ Corrosion inhibitor' '✓ Full system flush'. "
            "At the bottom, slim dark navy banner: white text 'Better Call Wes · Included as Standard'. "
            "The authentic hands-on photo must remain the focus."
        ),
    },
    {
        "id": "magnetic_filter_sludge",
        "name": "Magnetic filter — black sludge shock (system health hook)",
        "aspect_ratio": "4:5",
        "base_image": str(WORK_IMAGES / "IMG_0760.jpg"),
        "prompt": (
            "Keep this photo of a magnetic system filter being cleaned — showing thick black iron oxide sludge — completely unchanged. "
            "Add a dark navy semi-transparent banner at the top of the image: "
            "bold white text 'This was circulating in their boiler.' "
            "At the bottom, solid dark navy banner: "
            "bold white text 'Magnetic Filter Fitted From £150', "
            "smaller white text 'Protects your boiler · Better Call Wes · Southampton'. "
            "The shocking sludge photo must stay fully visible and dominant."
        ),
    },
    {
        "id": "system_install_cylinder",
        "name": "System install — boiler + unvented cylinder (upsell)",
        "aspect_ratio": "4:5",
        "base_image": str(WORK_IMAGES / "IMG_1157.JPG"),
        "prompt": (
            "Keep this photo of a boiler and large unvented hot water cylinder with neat copper pipework unchanged. "
            "Add a clean white rounded-corner information panel overlaid in the top-left corner: "
            "bold dark navy heading 'System Boiler + Unvented Cylinder', "
            "then in smaller dark navy text: '✓ Unlimited hot water' '✓ Mains pressure to every tap' '✓ No cold showers'. "
            "At the bottom, slim dark navy banner: white text 'Better Call Wes · Southampton · Gas Safe'. "
            "The professional installation photo must remain the dominant element."
        ),
    },
]


def main():
    from kie_client import KieClient

    kie = KieClient()

    credits = kie.check_credits()
    print(f"\n💳 Kie AI credits: {credits}")
    print(f"🖼  Generating {len(ADS)} ads using real photo bases...\n")

    results = []

    for ad in ADS:
        print(f"{'='*60}")
        print(f"📸 {ad['name']} ({ad['aspect_ratio']})")

        base_path = ad.get("base_image")
        if base_path and not Path(base_path).exists():
            print(f"  ⚠️  Base image not found: {base_path}")
            print(f"  Skipping...")
            continue

        try:
            # Upload base image to catbox for Kie AI
            base_url = None
            if base_path:
                print(f"  📤 Uploading base photo: {Path(base_path).name}")
                base_url = upload_to_catbox(base_path)
                print(f"  🔗 Base URL: {base_url}")

            url = kie.generate_image(
                prompt=ad["prompt"],
                image_input_url=base_url,
                aspect_ratio=ad["aspect_ratio"],
                resolution="2K",
                output_format="jpg",
            )
            print(f"  ✅ Generated: {url[:60]}...")

            filename = f"v2_{ad['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            local_path = ADS_DIR / filename
            download_image(url, local_path)
            print(f"  💾 Saved: social/ads/v2/{filename}")

            results.append({
                "id": ad["id"],
                "name": ad["name"],
                "aspect_ratio": ad["aspect_ratio"],
                "base_image": base_path,
                "local_file": str(local_path),
                "kie_url": url,
                "generated_at": datetime.now().isoformat(),
            })

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            results.append({"id": ad["id"], "name": ad["name"], "error": str(e)})

        print()

    manifest_path = ADS_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)

    credits_after = kie.check_credits()
    success = len([r for r in results if "local_file" in r])
    print(f"{'='*60}")
    print(f"\n✅ Done. {success}/{len(ADS)} generated.")
    print(f"📁 Files saved to: website/social/ads/v2/")
    print(f"💳 Credits used: {credits - credits_after} | Remaining: {credits_after}")
    print(f"\nUpload from website/social/ads/v2/ to Meta Ads Manager.")


if __name__ == "__main__":
    main()
