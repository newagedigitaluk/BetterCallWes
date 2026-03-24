"""
Image picker for social posts.

Selects real photos from the Better Call Wes image library based on
the post's image_type. Returns None for 'ai' image type (triggers Kie AI
generation without a base image).

Image sources:
  brand  → Brand Images/         (photos of Wes)
  work   → Brand Images/Work Images/  (job/site photos)
  asset  → Website/assets/images/     (service graphics)
  ai     → None (fully AI-generated)
"""

import os
import random
from pathlib import Path

# Resolve project root (parent of this file's directory)
PROJECT_ROOT = Path(__file__).parent.parent

BRAND_DIR = PROJECT_ROOT / "Brand Images"
WORK_DIR  = PROJECT_ROOT / "Brand Images" / "Work Images"
ASSET_DIR = PROJECT_ROOT / "Website" / "assets" / "images"

# Asset images mapped by topic keywords for smarter selection
ASSET_KEYWORD_MAP = {
    "boiler": ["boiler-repair.webp", "boiler-repair.png"],
    "heating": ["heating-radiator.webp", "heating-radiator.png"],
    "radiator": ["heating-radiator.webp", "heating-radiator.png"],
    "plumbing": ["plumbing-repairs.webp", "plumbing-repairs.png", "copper-pipework.webp"],
    "pipe": ["copper-pipework.webp", "copper-pipework.png"],
    "shower": ["bathroom-shower.webp", "bathroom-shower.png"],
    "bathroom": ["bathroom-shower.webp", "bathroom-shower.png"],
    "gas": ["gas-safety.webp", "gas-safety.png"],
    "landlord": ["gas-safety.webp", "gas-safety.png"],
    "certificate": ["gas-safety.webp", "gas-safety.png"],
    "local": ["southampton-cityscape.webp", "southampton-cityscape.png", "van-work.webp"],
    "southampton": ["southampton-cityscape.webp", "southampton-cityscape.png"],
    "van": ["van-work.webp", "van-work.png"],
    "tools": ["plumber-tools.webp", "plumber-tools.png"],
}

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _list_images(directory: Path) -> list:
    """Return sorted list of supported image file paths in a directory."""
    if not directory.exists():
        return []
    files = []
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(str(f))
    return sorted(files)


def pick(image_type: str, used_log: list = None, topic: str = "") -> str | None:
    """
    Pick a real image file path based on image_type.

    Args:
        image_type: 'brand', 'work', 'asset', or 'ai'
        used_log:   List of recently used file paths to avoid repeating
        topic:      Post topic string used to select relevant asset images

    Returns:
        Absolute file path string for brand/work/asset types.
        None for 'ai' type (caller should use Kie AI prompt-only generation).
    """
    if image_type == "ai":
        return None

    used_log = used_log or []

    if image_type == "brand":
        candidates = _list_images(BRAND_DIR)
    elif image_type == "work":
        candidates = _list_images(WORK_DIR)
    elif image_type == "asset":
        candidates = _pick_asset_candidates(topic)
    else:
        print(f"  [ImagePicker] Unknown image_type '{image_type}', defaulting to brand.")
        candidates = _list_images(BRAND_DIR)

    if not candidates:
        print(f"  [ImagePicker] No images found for type '{image_type}'. Falling back to brand.")
        candidates = _list_images(BRAND_DIR)

    if not candidates:
        print("  [ImagePicker] No images found at all. Will generate via AI.")
        return None

    # Prefer unused images; fall back to all if all have been used
    unused = [c for c in candidates if c not in used_log]
    pool = unused if unused else candidates

    chosen = random.choice(pool)
    print(f"  [ImagePicker] Selected: {os.path.basename(chosen)}")
    return chosen


def _pick_asset_candidates(topic: str) -> list:
    """Select asset images relevant to the post topic."""
    topic_lower = topic.lower()

    # Try topic-matched assets first
    for keyword, filenames in ASSET_KEYWORD_MAP.items():
        if keyword in topic_lower:
            matched = []
            for filename in filenames:
                path = ASSET_DIR / filename
                if path.exists():
                    matched.append(str(path))
            if matched:
                return matched

    # Fall back to all available asset images
    return _list_images(ASSET_DIR)


if __name__ == "__main__":
    # Test the picker
    print("Brand image:", pick("brand", topic="Gas Safe"))
    print("Work image: ", pick("work", topic="boiler repair"))
    print("Asset image:", pick("asset", topic="boiler repair"))
    print("AI image:   ", pick("ai", topic="pricing"))
