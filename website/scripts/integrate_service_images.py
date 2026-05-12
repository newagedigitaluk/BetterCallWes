"""Insert AI-generated work photos into the 22 service pages that lacked them.

For each <slug>.webp now living in website/site/assets/images/, finds the
corresponding service page at website/site/services/<slug>.html and inserts
a single 'Real work' image block before the mid-page CTA.

Pages that already have a multi-photo work strip (the 7 priority pages
enhanced earlier) are skipped — they already have their own imagery.

Usage:
    python3 website/scripts/integrate_service_images.py            # apply
    python3 website/scripts/integrate_service_images.py --dry-run  # preview
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
SERVICES_DIR = ROOT / "website" / "site" / "services"
IMAGES_DIR = ROOT / "website" / "site" / "assets" / "images"

# Captions per page — short, honest, area-where-possible
CAPTIONS: dict[str, str] = {
    "boiler-fitting": "Worcester combi swap, Southampton",
    "boiler-systems": "Full system + cylinder install",
    "central-heating": "Combi diagnostic with multimeter",
    "combi-boiler-installations": "Combi install, mid-pipework",
    "gas-appliance-servicing": "Gas hob service, kitchen worktop",
    "gas-leak-detection": "Electronic leak detection, behind the cooker",
    "gas-pipe-installation": "Copper gas pipe — fresh cut",
    "gas-services": "Gas safety test at the meter",
    "heating-controls": "Hive thermostat install",
    "outdoor-taps": "Garden bib tap, fresh install",
    "pipe-leak-repair": "Leak detection under the sink",
    "power-flushing": "Power flush with Kamco kit + MagnaClean",
    "radiators": "Radiator balancing, hallway",
    "shower-repair": "Shower cartridge replacement",
    "showers": "New chrome mixer fitted to tile",
    "small-plumbing-jobs": "Flexi connector replacement under the sink",
    "smart-controls": "Nest Learning Thermostat install",
    "system-flushing": "MagnaClean cleanout — sludge drained",
    "tap-repair": "Kitchen tap cartridge swap",
    "taps": "New chrome mixer, under-sink tightening",
    "toilet-repair": "Cistern lid up, fill valve check",
    "toilet-repairs": "Brass fill valve replacement",
    "water-tank-services": "Unvented cylinder pressure check",
}

MARKER_BEGIN = "<!-- BEGIN WORK PHOTO -->"
MARKER_END = "<!-- END WORK PHOTO -->"
EXISTING_BLOCK_RE = re.compile(
    re.escape(MARKER_BEGIN) + r".*?" + re.escape(MARKER_END), re.DOTALL
)
# The 7 priority pages already have a 3-image strip; do not double up.
PRIORITY_MARKER = "<!-- BEGIN WORK PHOTOS -->"


def block_html(slug: str, caption: str) -> str:
    return f"""
{MARKER_BEGIN}
<section class="section section-gray">
  <div class="container" style="max-width: 800px;">
    <div class="section-header">
      <div class="section-label">REAL WORK</div>
      <h2>This is what I actually do</h2>
    </div>
    <figure style="margin: 0;">
      <img src="../assets/images/{slug}.webp" alt="Better Call Wes — {caption}" loading="lazy" decoding="async" style="width: 100%; max-width: 600px; display: block; margin: 0 auto; height: auto; border-radius: var(--radius-md, 8px); box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.08));">
      <figcaption style="margin-top: 0.75rem; font-size: 0.95rem; color: var(--text-body); text-align: center;">{caption}</figcaption>
    </figure>
  </div>
</section>
{MARKER_END}
""".strip()


def process(slug: str, caption: str, dry: bool) -> str:
    html_path = SERVICES_DIR / f"{slug}.html"
    img_path = IMAGES_DIR / f"{slug}.webp"
    if not html_path.exists():
        return "no html"
    if not img_path.exists():
        return "no image yet"

    text = html_path.read_text(encoding="utf-8")

    # Skip if already has the 7-priority work strip
    if PRIORITY_MARKER in text:
        return "skip (priority page has 3-image strip)"

    block = block_html(slug, caption)

    if EXISTING_BLOCK_RE.search(text):
        new_text = EXISTING_BLOCK_RE.sub(block, text, count=1)
        action = "replaced"
    else:
        anchor = "<!-- BEGIN MID CTA -->"
        idx = text.find(anchor)
        if idx < 0:
            return "no mid-CTA anchor"
        new_text = text[:idx] + block + "\n\n" + text[idx:]
        action = "inserted"

    if not dry:
        html_path.write_text(new_text, encoding="utf-8")
    return action


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", help="comma-separated slugs")
    args = parser.parse_args()

    slugs = (
        [s.strip() for s in args.only.split(",") if s.strip()]
        if args.only
        else list(CAPTIONS.keys())
    )

    for slug in slugs:
        caption = CAPTIONS.get(slug, slug.replace("-", " ").title())
        result = process(slug, caption, args.dry_run)
        prefix = "[dry] " if args.dry_run else ""
        print(f"{prefix}{slug}: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
