"""Batch-generate AI service-page images via Higgsfield GPT Image 2.

Each image uses the same reference policy (saved in memory):
- Master character sheet
- 5 real reference photos from website/Brand Images/
- No physical description of Wes — the references do that work
- Scene-specific prompt only

Output: website/site/assets/images/<slug>.webp (1024x1024, ~80-150 KB each)

Usage:
    python3 website/scripts/generate_service_images.py            # all missing
    python3 website/scripts/generate_service_images.py --only smart-controls,radiators
    python3 website/scripts/generate_service_images.py --dry-run  # preview prompts only
    python3 website/scripts/generate_service_images.py --redo radiators  # regenerate one
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1].parent
SITE_IMG = ROOT / "website" / "site" / "assets" / "images"
BRAND_IMG = ROOT / "website" / "Brand Images"

MASTER_SHEET = BRAND_IMG / "Character Sheet" / "character-sheet-v2-expanded-refs.png"
SUPPORTING_REFS = [
    BRAND_IMG / "IMG_0982.JPG",
    BRAND_IMG / "IMG_0984.JPG",
    BRAND_IMG / "IMG_1244.JPG",
    BRAND_IMG / "IMG_1250.JPG",
    BRAND_IMG / "IMG_1257.JPG",
]

# Common prompt prefix and suffix used for every scene
PROMPT_PREFIX = (
    "Phone photo, candid documentary realism. The person from the reference photos, "
    "wearing the navy work polo and dark work trousers visible in the references, "
)
PROMPT_SUFFIX = (
    " Real cluttered UK domestic environment, natural overhead bulb lighting with a "
    "slightly warm cast. Slight grain. Imperfect framing as if taken by a customer "
    "with their phone. No posed smile. No magazine polish. Square 1:1 framing."
)

# Scene-specific middles, keyed by service-page slug (filename without .html)
SCENES: dict[str, str] = {
    "boiler-fitting": (
        "lifting and positioning a brand new white Worcester Bosch combi boiler "
        "onto a wall bracket in a domestic utility room. Both hands support the "
        "boiler from underneath as he aligns it with the wall fixings. A spirit "
        "level rests on the worktop next to him. Focused expression."
    ),
    "boiler-systems": (
        "standing back with hands on his hips, surveying a freshly installed "
        "Worcester system boiler with an adjacent unvented hot water cylinder "
        "and neat copper manifold pipework in a domestic utility room. Job complete."
    ),
    "central-heating": (
        "kneeling beside a wall-mounted white Worcester combi boiler in a "
        "domestic utility room. The boiler's front control cover is open. He is "
        "holding a digital multimeter probe against the wiring loom inside the "
        "boiler. Tool roll on the floor next to him."
    ),
    "combi-boiler-installations": (
        "kneeling at a freshly mounted Worcester combi boiler, routing a copper "
        "pipe up to the boiler's lower fittings. A pipe slice tool and a small "
        "soldering torch lie on a dust sheet on the floor. Real domestic utility "
        "room."
    ),
    "gas-appliance-servicing": (
        "lifting a four-burner stainless steel gas hob carefully out of a "
        "kitchen worktop cutout, both hands on the hob casing. A gas spanner "
        "and a new gas hose lie on the counter next to the cutout."
    ),
    "gas-pipe-installation": (
        "kneeling on the floor of a domestic utility room, cutting copper gas "
        "pipe with a small pipe slice tool. Two short copper offcuts and "
        "several brass compression fittings rest on a dust sheet next to him."
    ),
    "gas-services": (
        "standing at a domestic gas meter cabinet on an exterior wall, with a "
        "clipboard in one hand and a manometer connected to the meter's test "
        "point with the other. Focused expression."
    ),
    "heating-controls": (
        "standing in a hallway, mounting a Hive smart thermostat onto the wall "
        "with a screwdriver. The plastic mounting plate is already on the wall; "
        "the round display unit is in his other hand."
    ),
    "outdoor-taps": (
        "kneeling beside an outside garden wall, installing a brass garden bib "
        "tap. A cordless drill is on the patio next to him. Copper pipe is "
        "visible coming through the wall behind the tap. Real garden environment."
    ),
    "pipe-leak-repair": (
        "crouched in front of an open kitchen sink cupboard, head tilted to look "
        "up at the pipework underneath. A torch is in one hand and a slip-joint "
        "pliers in the other. A small towel and a plastic tub catch drips below "
        "the pipe joint. Cupboard contents visible behind him."
    ),
    "power-flushing": (
        "kneeling beside a wall-mounted combi boiler, connecting orange Kamco "
        "power-flush hoses to the boiler's flow and return valves. A black "
        "Adey MagnaClean magnetic filter is visible on the system pipework. "
        "Dust sheets cover the floor."
    ),
    "radiators": (
        "kneeling next to a white panel radiator in a domestic hallway, holding "
        "a flathead screwdriver to the radiator's lockshield valve, one hand "
        "resting on top of the radiator. Real domestic hallway visible behind."
    ),
    "shower-repair": (
        "standing in front of a tiled bathroom shower wall, replacing a chrome "
        "shower mixer cartridge. The mixer faceplate is removed and lying on a "
        "small towel on the floor. The new ceramic cartridge is in his hand."
    ),
    "showers": (
        "fitting a new chrome shower mixer onto a tiled bathroom wall, a spirit "
        "level held against the mixer to check it's straight. Real domestic "
        "bathroom environment with tiles and grout visible."
    ),
    "small-plumbing-jobs": (
        "kneeling on a kitchen floor, both hands reaching up under the sink to "
        "tighten a flexi tap connector with a basin spanner. A small puddle of "
        "drip water on a towel under the U-bend. Cupboard contents partially "
        "visible."
    ),
    "smart-controls": (
        "standing at a hallway wall, screwing a round Nest Learning Thermostat "
        "onto the wall mounting plate. A homeowner's hand (not the homeowner's "
        "face, just hand and forearm) is visible to the side holding a phone "
        "with the Nest app open."
    ),
    "system-flushing": (
        "kneeling on a dust sheet beside a wall-mounted boiler, opening an Adey "
        "MagnaClean magnetic filter cartridge. Dark sludgy water is draining "
        "from the filter into a plastic bucket below. Disposable nitrile "
        "gloves on his hands."
    ),
    "tap-repair": (
        "standing at a kitchen sink, mid-task replacing a chrome kitchen tap "
        "cartridge. The tap head is disassembled, the old ceramic cartridge in "
        "his hand. New replacement parts laid out on the draining board next to him."
    ),
    "taps": (
        "crouched under a kitchen sink, both hands hand-tightening a brand new "
        "chrome mixer tap from underneath, looking up at the new tap installed "
        "from above. Cupboard interior visible around him."
    ),
    "toilet-repair": (
        "standing beside a white domestic toilet with the cistern lid lifted "
        "off and resting on the seat. He is looking down at the brass fill valve "
        "and float assembly inside the cistern. Tool bag visible on the floor."
    ),
    "toilet-repairs": (
        "kneeling beside a white domestic toilet, both hands lowering a new brass "
        "fill valve into the open cistern. The old fill valve and worn flapper "
        "rest on a small towel on the floor next to him."
    ),
    "water-tank-services": (
        "standing in an airing cupboard, inspecting a large white unvented hot "
        "water cylinder with a foam insulation jacket. He is holding a pressure "
        "gauge in his hand, the gauge dial visible. Pipework visible around the "
        "cylinder."
    ),
}


def already_exists(slug: str) -> bool:
    return (SITE_IMG / f"{slug}.webp").exists()


def generate_one(slug: str, scene: str, redo: bool = False) -> tuple[bool, str]:
    out = SITE_IMG / f"{slug}.webp"
    if out.exists() and not redo:
        return True, "skipped (exists)"

    prompt = PROMPT_PREFIX + scene + PROMPT_SUFFIX
    cmd = [
        "higgsfield", "generate", "create", "gpt_image_2",
        "--prompt", prompt,
        "--image", str(MASTER_SHEET),
        *(arg for ref in SUPPORTING_REFS for arg in ("--image", str(ref))),
        "--aspect_ratio", "1:1",
        "--quality", "high",
        "--resolution", "1k",
        "--wait",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if result.returncode != 0:
        return False, f"cli failed: {result.stderr.strip()[:200]}"
    url = result.stdout.strip().split("\n")[-1]
    if not url.startswith("https://"):
        return False, f"no URL: {url[:200]}"

    # Download PNG to tmp, convert to WebP, save to assets
    tmp_png = Path(f"/tmp/higgs-{slug}.png")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            tmp_png.write_bytes(resp.read())
    except Exception as e:
        return False, f"download failed: {e}"

    img = Image.open(tmp_png)
    img.thumbnail((1024, 1024), Image.LANCZOS)
    img.save(out, "webp", quality=82, method=6)
    tmp_png.unlink(missing_ok=True)
    return True, f"saved {out.stat().st_size // 1024}KB"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated slugs (default: all missing)")
    parser.add_argument("--redo", help="comma-separated slugs to regenerate even if file exists")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.only:
        targets = [s.strip() for s in args.only.split(",") if s.strip()]
    else:
        targets = list(SCENES.keys())

    redo = set(s.strip() for s in (args.redo or "").split(",") if s.strip())

    if args.dry_run:
        for slug in targets:
            if slug not in SCENES:
                print(f"  UNKNOWN slug: {slug}")
                continue
            status = "EXISTS" if already_exists(slug) and slug not in redo else "WILL GENERATE"
            print(f"  [{status}] {slug}")
        return 0

    total_to_do = sum(
        1 for s in targets
        if s in SCENES and (not already_exists(s) or s in redo)
    )
    print(f"Plan: generate {total_to_do} image(s). Estimated cost: ~{total_to_do * 4} credits.\n")

    successes = 0
    failures = 0
    for i, slug in enumerate(targets, 1):
        if slug not in SCENES:
            print(f"[{i}/{len(targets)}] UNKNOWN {slug}")
            failures += 1
            continue
        scene = SCENES[slug]
        print(f"[{i}/{len(targets)}] {slug} ...")
        ok, msg = generate_one(slug, scene, redo=slug in redo)
        if ok:
            print(f"  OK: {msg}")
            successes += 1
        else:
            print(f"  FAIL: {msg}", file=sys.stderr)
            failures += 1
        # Small pacing pause to be polite to the API
        time.sleep(1)

    print(f"\nDone: {successes} generated, {failures} failed.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
