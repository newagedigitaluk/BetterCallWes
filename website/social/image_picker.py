"""
Image picker for social posts — catalogue-driven version.

Picks the right photo from the library based on the post's `image_hint`
field (e.g. "asset:boiler", "work:powerflush", "brand:wes_portrait").

The matching is driven by `image_catalogue.json` — a hand-built tag matrix
of every asset image with what it depicts, who's in frame, and which hints
it's suitable for. This stops the old failure mode where a generic "boiler"
post would pull a photo of Wes mid-install.

Selection rules:
  1. Look up the `image_hint` in the catalogue's _hint_coverage map.
  2. From the candidate list, prefer images not in `used_log` (dedup).
  3. Random choice among remaining candidates.
  4. Fall back to legacy directory scan only if catalogue has no entry.
  5. Never return an image tagged "do-not-use".

For `image_type` (the higher-level field):
  brand → ALSO falls back to Brand Images/ if no catalogue match
  work  → ALSO falls back to Brand Images/Work Images/ if no catalogue match
  ai    → returns None (Kie AI prompt-only generation)
"""

import json
import os
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CATALOGUE_PATH = Path(__file__).parent / "image_catalogue.json"

BRAND_DIR = PROJECT_ROOT / "Brand Images"
WORK_DIR  = PROJECT_ROOT / "Brand Images" / "Work Images"
ASSET_DIR = PROJECT_ROOT / "site" / "assets" / "images"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def infer_image_hint(post: dict) -> str:
    """
    Determine the correct image_hint for a post.

    Priority:
      1. Explicit `image_hint` on the post (set by the batch builder) — trust it.
      2. Pillar + topic-keyword inference (robust fallback so personal posts
         show Wes, local posts show the van, testimonials show a review card,
         etc. — even if a future batch forgets to set image_hint).
      3. Service-slug map (last resort, subject-only).

    This exists because the original 90-batch shipped WITHOUT image_hint, so
    the old slug-only fallback sent every personal/Wes/testimonial post to a
    generic boiler image. Pillar-awareness fixes that at the root.
    """
    explicit = post.get("image_hint")
    if explicit:
        return explicit

    pillar = (post.get("pillar") or "").lower()
    topic = (post.get("topic") or "").lower()
    image_type = post.get("image_type", "ai")
    slug = post.get("service_slug", "")

    def any_in(*words):
        return any(w in topic for w in words)

    # --- Pillar-driven routing (the important part) ---
    if pillar == "personal":
        if any_in("van", "carry"):
            return "asset:van"
        if any_in("phone", "whatsapp", "progress photo", "video"):
            return "brand:wes_with_phone"
        if any_in("intro", "i'm wes", "im wes", "left big", "wish", "quote", "why i"):
            return "brand:wes_portrait"
        return "brand:wes_with_tools"

    if pillar == "trust":
        if any_in("testimonial", "review", "happy customer"):
            return "review_card"
        if any_in("guarantee", "after-hours", "after hours", "promise"):
            return "brand:wes_portrait"
        if any_in("price", "pricing", "bill", "quote", "cost"):
            return "ai"
        return "brand:wes_portrait"

    if pillar == "emergency":
        if any_in("whatsapp", "video", "phone"):
            return "brand:wes_with_phone"
        if any_in("burst", "pipe", "leak"):
            return "asset:pipe"
        if any_in("same-day", "same day", "area", "so14", "cover"):
            return "asset:van"
        return "brand:wes_portrait"

    if pillar == "local":
        if any_in("cp12", "landlord", "gas", "certificate"):
            return "asset:gas"
        if any_in("worst", "install", "fitted"):
            return "work:install"
        return "asset:van_southampton"   # geographic coverage posts → van / skyline

    if pillar == "before_after":
        # Genuine before/after pairs we actually have:
        if any_in("tap"):
            return "before_after:tap"      # tap-before/after pair
        if any_in("heat exchanger", "service", "burner"):
            return "asset:heatex"          # clean-vs-dirty heatex pair
        if any_in("sludge", "flush", "inhibitor", "magnetic", "filter"):
            return "work:powerflush"       # Wes + sludge bucket (delivers the reveal)
        if any_in("shower"):
            return "work:shower"
        if any_in("radiator", "rad "):
            return "work:radiator_swap"
        # else fall through to slug map

    # --- Service-slug map (subject-only last resort) ---
    slug_to_hint = {
        "boiler-repair": "asset:boiler", "boiler-service": "asset:boiler",
        "boiler-install": "work:install", "new-boiler": "asset:boiler",
        "combi-install": "work:install",
        "power-flush": "work:powerflush" if image_type == "work" else "asset:heatex",
        "central-heating": "asset:radiator", "gas-safety": "asset:gas",
        "gas-leak": "asset:gas", "cp12": "asset:gas", "plumbing": "asset:plumbing",
        "radiators": "asset:radiator", "smart-controls": "asset:smart",
        "heating-controls": "asset:smart",
        "tap-repair": "asset:tap" if image_type == "asset" else "work:tap_install",
        "pipe-leak": "asset:pipe" if image_type == "asset" else "work:pipe_repair",
        "shower-repair": "asset:shower" if image_type == "asset" else "work:shower",
        "toilet-repair": "work:toilet_repair", "system-flush": "work:powerflush",
    }
    return slug_to_hint.get(slug, f"{image_type}:generic")


def _load_catalogue() -> dict:
    if not CATALOGUE_PATH.exists():
        return {"images": {}, "_hint_coverage": {}}
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def _list_images(directory: Path) -> list:
    if not directory.exists():
        return []
    return sorted(
        str(f) for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _is_blocked(filename: str, catalogue: dict) -> bool:
    """Return True if the image is tagged do-not-use."""
    entry = catalogue.get("images", {}).get(filename, {})
    return "do-not-use" in entry.get("tags", [])


def pick(image_type: str, used_log: list = None, topic: str = "",
         image_hint: str = "") -> str | None:
    """
    Pick a real image file path based on image_hint (preferred) or image_type.

    Args:
        image_type:  "brand" | "work" | "asset" | "ai"
        used_log:    List of recently-used absolute paths to avoid repeating
        topic:       Post topic (legacy hint — only used if image_hint empty)
        image_hint:  The post's `image_hint` field (e.g. "asset:boiler"),
                     which is what the catalogue actually keys on.

    Returns:
        Absolute file path string, or None for "ai" type.
    """
    if image_type == "ai":
        return None

    used_log = used_log or []
    catalogue = _load_catalogue()
    hint_map = catalogue.get("_hint_coverage", {})

    # Try precise hint-based match first
    candidates = []
    if image_hint and image_hint in hint_map and isinstance(hint_map[image_hint], list):
        for filename in hint_map[image_hint]:
            if _is_blocked(filename, catalogue):
                continue
            full = ASSET_DIR / filename
            if full.exists():
                candidates.append(str(full))

    if candidates:
        unused = [c for c in candidates if c not in used_log]
        pool = unused if unused else candidates
        chosen = random.choice(pool)
        print(f"  [ImagePicker] hint='{image_hint}' → {os.path.basename(chosen)}")
        return chosen

    # No catalogue match — fall back by image_type
    if image_type == "brand":
        candidates = _list_images(BRAND_DIR)
    elif image_type == "work":
        candidates = _list_images(WORK_DIR)
    elif image_type == "asset":
        # Catalogued asset images only (block do-not-use). On fallback, prefer
        # anonymous (person=null) shots so generic posts don't accidentally
        # use a Wes-in-action image.
        anon = []
        with_person = []
        for filename, entry in catalogue.get("images", {}).items():
            if _is_blocked(filename, catalogue):
                continue
            full = ASSET_DIR / filename
            if not full.exists():
                continue
            if entry.get("person") in (None, "null"):
                anon.append(str(full))
            else:
                with_person.append(str(full))
        candidates = anon if anon else with_person
        if not candidates:
            candidates = _list_images(ASSET_DIR)
    else:
        print(f"  [ImagePicker] Unknown image_type '{image_type}', defaulting to brand")
        candidates = _list_images(BRAND_DIR)

    if not candidates:
        print(f"  [ImagePicker] No candidates for hint='{image_hint}' type='{image_type}' — caller should use AI generation")
        return None

    unused = [c for c in candidates if c not in used_log]
    pool = unused if unused else candidates
    chosen = random.choice(pool)
    print(f"  [ImagePicker] fallback (type={image_type}, hint={image_hint or 'none'}) → {os.path.basename(chosen)}")
    return chosen


if __name__ == "__main__":
    # Spot-check the most common hints from the 90-post batch
    print("\n=== Picker tests ===\n")
    test_hints = [
        ("asset", "asset:boiler"),
        ("asset", "asset:radiator"),
        ("asset", "asset:tap"),
        ("asset", "asset:gas"),
        ("asset", "asset:heatex"),
        ("work",  "work:powerflush"),
        ("work",  "work:install"),
        ("work",  "work:shower"),
        ("brand", "brand:wes_portrait"),
        ("brand", "brand:wes_with_tools"),
        ("brand", "brand:wes_with_phone"),
        ("brand", "brand:wes_with_van"),       # known no-match — should fall back
        ("asset", "asset:nonexistent"),         # missing hint — should fall back
    ]
    for t, h in test_hints:
        print(f"  type={t:<6} hint={h:<28} →", end=" ")
        result = pick(t, topic="", image_hint=h)
        print(os.path.basename(result) if result else "None")
