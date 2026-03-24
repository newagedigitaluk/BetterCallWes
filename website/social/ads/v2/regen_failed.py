"""Regenerate the 2 failed ads from generate_ads_v2.py."""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

ADS_DIR = Path(__file__).parent
PROJECT_ROOT = ADS_DIR.parent.parent.parent  # website/social/ads/v2 -> website/
WORK_IMAGES = PROJECT_ROOT / "Brand Images" / "Work Images"

sys.path.insert(0, str(PROJECT_ROOT / "social"))


def upload_to_catbox(file_path: str) -> str:
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


ADS = [
    {
        "id": "smart_boiler",
        "name": "Smart boiler — Worcester CDi circular display (upgrade hook)",
        "aspect_ratio": "1:1",
        "base_image": str(WORK_IMAGES / "IMG_4813.jpg"),  # lowercase .jpg
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
]


def main():
    from kie_client import KieClient

    kie = KieClient()
    credits = kie.check_credits()
    print(f"\n💳 Kie AI credits: {credits}")
    print(f"🖼  Regenerating 2 failed ads...\n")

    for ad in ADS:
        print(f"{'='*60}")
        print(f"📸 {ad['name']} ({ad['aspect_ratio']})")

        base_path = ad.get("base_image")
        if not Path(base_path).exists():
            print(f"  ⚠️  Base image not found: {base_path}")
            continue

        try:
            print(f"  📤 Uploading: {Path(base_path).name}")
            base_url = upload_to_catbox(base_path)
            print(f"  🔗 {base_url}")

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
            print(f"  💾 Saved: {filename}")

        except Exception as e:
            print(f"  ❌ Failed: {e}")

        print()

    credits_after = kie.check_credits()
    print(f"💳 Credits used: {credits - credits_after} | Remaining: {credits_after}")


if __name__ == "__main__":
    main()
