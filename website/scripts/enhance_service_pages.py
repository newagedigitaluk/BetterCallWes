"""Apply Tier-1 + Tier-2 conversion improvements to every service page.

For every .html in website/site/services/:
  - Ensure the floating WhatsApp CTA is present
  - Add a trust strip (Gas Safe • 4.9★ • 12-month guarantee • SO14–SO51)
    immediately after the hero
  - Inject the GHL reviews iframe widget mid-page (before the FAQ section
    where present, otherwise before the footer)
  - Add a mid-page WhatsApp CTA strip
  - Add a 'Recently worked in nearby areas' pill list
For the 7 priority pages, additionally:
  - Add a 'Real recent work' image strip with 3 photos

H1 rewrites for the weak/buggy pages are handled in a small dict — these
are scoped per-page and applied verbatim.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
SERVICES = SITE / "services"

H1_REWRITES = {
    "boiler-installation.html": "Boiler Installation in Southampton",
    "new-boiler.html": "New Boilers in Southampton — From £2,100 Fitted",
    "gas-safety-check.html": "Gas Safety Checks in Southampton — £90 Same-Week",
    "landlord-gas-safety-certificates.html": "Landlord Gas Safety Certificate (CP12) in Southampton — £90",
    "boiler-repair.html": "Boiler Repair in Southampton — £100 Diagnostic, Same Visit",
    "boiler-servicing.html": "Boiler Servicing in Southampton — £100 Annual Service",
    "plumbing-repairs.html": "Plumbing Repairs in Southampton — £100 First Hour",
}

PRIORITY_PAGES_WITH_PHOTOS = {
    "boiler-repair.html": [
        ("boiler-heatex-clean-vs-dirty.webp", "Heat exchanger — old vs new"),
        ("stripped-old-boiler.webp", "Old unit removed, ready for swap"),
        ("neat-copper-manifold.webp", "Neat copper pipework, every time"),
    ],
    "boiler-servicing.html": [
        ("boiler-heatex-clean-vs-dirty.webp", "Why annual servicing matters"),
        ("powerflush-kit.webp", "Right kit on the van"),
        ("neat-copper-manifold.webp", "Quality workmanship signature"),
    ],
    "boiler-installation.html": [
        ("worcester-loft-install.webp", "Worcester Greenstar, loft install"),
        ("system-boiler-cylinder.webp", "System boiler + cylinder, neat run"),
        ("neat-copper-manifold.webp", "Pipework done properly"),
    ],
    "new-boiler.html": [
        ("worcester-loft-install.webp", "Worcester, modern flue route"),
        ("system-boiler-cylinder.webp", "Full system install"),
        ("stripped-old-boiler.webp", "Old removed, new fitted"),
    ],
    "gas-safety-check.html": [
        ("neat-copper-manifold.webp", "Gas pipework signed off"),
        ("worcester-loft-install.webp", "Same-day certificate by email"),
        ("system-boiler-cylinder.webp", "Every appliance tested"),
    ],
    "landlord-gas-safety-certificates.html": [
        ("neat-copper-manifold.webp", "Compliant gas install"),
        ("worcester-loft-install.webp", "CP12 issued same day"),
        ("system-boiler-cylinder.webp", "Two appliances, single fee"),
    ],
    "plumbing-repairs.html": [
        ("tap-before-corroded.webp", "Old corroded tap"),
        ("tap-after-chrome.webp", "Replaced same visit"),
        ("neat-copper-manifold.webp", "Pipework done properly"),
    ],
}

NEARBY_AREAS = [
    ("bitterne", "Bitterne"),
    ("portswood", "Portswood"),
    ("southampton", "Southampton"),
    ("bassett", "Bassett"),
    ("eastleigh", "Eastleigh"),
    ("hedge-end", "Hedge End"),
    ("chandlers-ford", "Chandler's Ford"),
    ("shirley", "Shirley"),
]

FLOATING_CTA = (
    '<a href="https://wa.me/447700155655" class="floating-cta">'
    '<i data-lucide="message-circle"></i> WhatsApp</a>'
)

MARKER_TRUST = "<!-- BEGIN TRUST STRIP -->"
MARKER_TRUST_END = "<!-- END TRUST STRIP -->"
MARKER_MID_CTA = "<!-- BEGIN MID CTA -->"
MARKER_MID_CTA_END = "<!-- END MID CTA -->"
MARKER_REVIEWS = "<!-- BEGIN REVIEWS WIDGET -->"
MARKER_REVIEWS_END = "<!-- END REVIEWS WIDGET -->"
MARKER_NEARBY = "<!-- BEGIN NEARBY AREAS -->"
MARKER_NEARBY_END = "<!-- END NEARBY AREAS -->"
MARKER_PHOTOS = "<!-- BEGIN WORK PHOTOS -->"
MARKER_PHOTOS_END = "<!-- END WORK PHOTOS -->"


def trust_strip_html() -> str:
    return f"""
{MARKER_TRUST}
<section style="background: var(--color-primary); padding: 1rem 0; border-top: 3px solid var(--color-accent);">
  <div class="container" style="display: flex; flex-wrap: wrap; gap: 1rem 2rem; justify-content: center; align-items: center; color: white; font-size: 0.9rem;">
    <span style="display: inline-flex; align-items: center; gap: 0.4rem;"><i data-lucide="shield-check" style="width: 18px; height: 18px; color: var(--color-accent);"></i> Gas Safe Registered</span>
    <span style="display: inline-flex; align-items: center; gap: 0.4rem;"><i data-lucide="star" style="width: 18px; height: 18px; color: var(--color-accent);"></i> 4.9&#9733; on Google (200+ reviews)</span>
    <span style="display: inline-flex; align-items: center; gap: 0.4rem;"><i data-lucide="award" style="width: 18px; height: 18px; color: var(--color-accent);"></i> 12-month workmanship guarantee</span>
    <span style="display: inline-flex; align-items: center; gap: 0.4rem;"><i data-lucide="map-pin" style="width: 18px; height: 18px; color: var(--color-accent);"></i> SO14&ndash;SO51</span>
  </div>
</section>
{MARKER_TRUST_END}
""".strip()


def mid_cta_html() -> str:
    return f"""
{MARKER_MID_CTA}
<section style="background: #25D366; padding: 2.5rem 0; text-align: center;">
  <div class="container" style="max-width: 720px;">
    <h3 style="color: white; margin: 0 0 0.5rem; font-size: 1.5rem;">Got a problem to sort?</h3>
    <p style="color: white; margin: 0 0 1.5rem; font-size: 1.05rem;">Send me a photo on WhatsApp &mdash; I&rsquo;ll come back with a fair quote.</p>
    <a href="https://wa.me/447700155655" style="display: inline-flex; align-items: center; gap: 0.5rem; background: white; color: #1a4d2e; padding: 0.85rem 1.75rem; border-radius: 999px; font-weight: 700; text-decoration: none; font-size: 1.05rem;"><i data-lucide="message-circle" style="width: 20px; height: 20px;"></i> WhatsApp 07700 155 655</a>
  </div>
</section>
{MARKER_MID_CTA_END}
""".strip()


def reviews_widget_html() -> str:
    return f"""
{MARKER_REVIEWS}
<section class="section section-gray">
  <div class="container" style="max-width: 900px;">
    <div class="section-header">
      <div class="section-label">REVIEWS</div>
      <h2>What Southampton homeowners say</h2>
    </div>
    <script type='text/javascript' src='https://i.bettercallwes.co.uk/reputation/assets/review-widget.js'></script>
    <iframe class='lc_reviews_widget' src='https://i.bettercallwes.co.uk/reputation/widgets/review_widget/7sUSfobemejSgrc2sd3v' frameborder='0' scrolling='no' style='min-width: 100%; width: 100%;'></iframe>
    <p style="text-align: center; margin-top: 1rem;"><a href="../reviews.html">See all reviews &rarr;</a></p>
  </div>
</section>
{MARKER_REVIEWS_END}
""".strip()


def nearby_areas_html() -> str:
    pills = "\n".join(
        f'      <a href="../locations/{slug}.html" style="display: inline-block; padding: 0.5rem 1rem; background: white; border: 1px solid var(--color-border, #e5e7eb); border-radius: 999px; color: var(--color-primary); text-decoration: none; font-size: 0.95rem; font-weight: 600;">{name}</a>'
        for slug, name in NEARBY_AREAS
    )
    return f"""
{MARKER_NEARBY}
<section class="section" style="padding: 2.5rem 0;">
  <div class="container" style="max-width: 900px; text-align: center;">
    <h3 style="margin-bottom: 0.5rem; font-size: 1.3rem;">Recently worked in nearby areas</h3>
    <p style="color: var(--text-body); margin-bottom: 1.5rem;">Click your area for an idea of what neighbours have asked me to fix.</p>
    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;">
{pills}
    </div>
  </div>
</section>
{MARKER_NEARBY_END}
""".strip()


def work_photos_html(photos: list[tuple[str, str]]) -> str:
    cards = "\n".join(
        f"""      <figure style="margin: 0;">
        <img src="../assets/images/{fname}" alt="{cap}" loading="lazy" decoding="async" style="width: 100%; height: 240px; object-fit: cover; border-radius: var(--radius-md, 8px); box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.08));">
        <figcaption style="margin-top: 0.6rem; font-size: 0.9rem; color: var(--text-body); text-align: center;">{cap}</figcaption>
      </figure>"""
        for fname, cap in photos
    )
    return f"""
{MARKER_PHOTOS}
<section class="section section-gray">
  <div class="container" style="max-width: 1100px;">
    <div class="section-header">
      <div class="section-label">REAL WORK</div>
      <h2>Recent jobs &mdash; not stock photos</h2>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
{cards}
    </div>
  </div>
</section>
{MARKER_PHOTOS_END}
""".strip()


def replace_or_insert(
    html: str,
    block: str,
    begin_marker: str,
    end_marker: str,
    after_pattern: re.Pattern | None,
    anchor: str | None = None,
) -> tuple[str, str]:
    """If the marker already exists, replace its content. Otherwise insert after
    `after_pattern` or before `anchor`. Returns (new_html, action_taken)."""
    pat = re.compile(re.escape(begin_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    if pat.search(html):
        return pat.sub(block, html, count=1), "replaced"
    if after_pattern:
        m = after_pattern.search(html)
        if m:
            end = m.end()
            return html[:end] + "\n\n" + block + "\n" + html[end:], "inserted-after-hero"
    if anchor:
        idx = html.find(anchor)
        if idx >= 0:
            return html[:idx] + block + "\n\n" + html[idx:], "inserted-before-anchor"
    return html, "no-anchor-skip"


def ensure_floating_cta(html: str) -> tuple[str, str]:
    if "floating-cta" in html:
        return html, "ok"
    foot = html.rfind("</body>")
    if foot < 0:
        return html, "no-body"
    return html[:foot] + FLOATING_CTA + "\n" + html[foot:], "added"


def rewrite_h1(html: str, new_h1: str) -> tuple[str, str]:
    # Handles both <h1>Text</h1> and <h1>Text <span>more</span></h1>
    pat = re.compile(r"(<h1[^>]*>)(.*?)(</h1>)", re.DOTALL)
    m = pat.search(html)
    if not m:
        return html, "no-h1"
    current = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    if current == new_h1:
        return html, "already-current"
    return pat.sub(lambda mm: mm.group(1) + new_h1 + mm.group(3), html, count=1), "rewritten"


# Match any hero section (covers `hero`, `hero hero-home`, `hero service-hero`, etc.)
HERO_END_RE = re.compile(
    r"(<section[^>]*class=\"[^\"]*\bhero\b[^\"]*\"[^>]*>.*?</section>)",
    re.DOTALL,
)
# For pages with no hero, fall back to inserting after the first H1-containing section
H1_SECTION_END_RE = re.compile(
    r"(<section[^>]*>\s*(?:<div[^>]*>\s*)*<h1[^>]*>.*?</section>)",
    re.DOTALL,
)
FAQ_START_RE = re.compile(
    r'<section[^>]*>\s*<div[^>]*>\s*<div class="section-header">\s*<div class="section-label">FAQS</div>',
    re.DOTALL,
)


def find_footer_anchor(html: str) -> str | None:
    """Return a substring to use as the 'before footer' anchor."""
    for anchor in ("<!-- Footer -->", "\n<footer", "<footer "):
        if anchor in html:
            return anchor
    return None


def process(path: Path, dry: bool) -> dict[str, str]:
    name = path.name
    html = path.read_text(encoding="utf-8")
    actions: dict[str, str] = {}

    # 1. H1 rewrite (if scheduled)
    if name in H1_REWRITES:
        html, action = rewrite_h1(html, H1_REWRITES[name])
        actions["h1"] = action

    # 2. Trust strip — try (a) hero close, (b) H1 section close, (c) </h1> close
    trust = trust_strip_html()
    H1_BARE_RE = re.compile(r"(<h1[^>]*>.*?</h1>)", re.DOTALL)
    for anchor_re in (HERO_END_RE, H1_SECTION_END_RE, H1_BARE_RE):
        html, action = replace_or_insert(
            html, trust, MARKER_TRUST, MARKER_TRUST_END, anchor_re
        )
        if action != "no-anchor-skip":
            break
    actions["trust_strip"] = action

    footer_anchor = find_footer_anchor(html)

    # 3. Reviews widget — insert BEFORE the FAQ section, else before footer
    reviews = reviews_widget_html()
    faq_match = FAQ_START_RE.search(html)
    if faq_match:
        anchor_text = html[faq_match.start():faq_match.start() + 80]
    else:
        anchor_text = footer_anchor
    html, action = replace_or_insert(
        html, reviews, MARKER_REVIEWS, MARKER_REVIEWS_END,
        after_pattern=None, anchor=anchor_text,
    )
    actions["reviews"] = action

    # 4. Mid-page CTA — directly before the reviews widget
    mid_cta = mid_cta_html()
    html, action = replace_or_insert(
        html, mid_cta, MARKER_MID_CTA, MARKER_MID_CTA_END,
        after_pattern=None, anchor=MARKER_REVIEWS,
    )
    actions["mid_cta"] = action

    # 5. Nearby areas — directly before footer
    nearby = nearby_areas_html()
    html, action = replace_or_insert(
        html, nearby, MARKER_NEARBY, MARKER_NEARBY_END,
        after_pattern=None, anchor=footer_anchor,
    )
    actions["nearby"] = action

    # 6. Work photos for priority pages only — directly before the mid-page CTA
    if name in PRIORITY_PAGES_WITH_PHOTOS:
        photos = work_photos_html(PRIORITY_PAGES_WITH_PHOTOS[name])
        html, action = replace_or_insert(
            html, photos, MARKER_PHOTOS, MARKER_PHOTOS_END,
            after_pattern=None, anchor=MARKER_MID_CTA,
        )
        actions["work_photos"] = action

    # 7. Floating WhatsApp CTA
    html, action = ensure_floating_cta(html)
    actions["floating_cta"] = action

    if not dry:
        path.write_text(html, encoding="utf-8")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", help="comma-separated page filenames (e.g. boiler-repair.html)")
    args = parser.parse_args()

    if args.only:
        pages = [SERVICES / f.strip() for f in args.only.split(",") if f.strip()]
    else:
        pages = sorted(SERVICES.glob("*.html"))

    for p in pages:
        if not p.exists():
            print(f"  MISSING {p.name}")
            continue
        actions = process(p, args.dry_run)
        prefix = "[dry] " if args.dry_run else ""
        compact = ", ".join(f"{k}={v}" for k, v in actions.items())
        print(f"{prefix}{p.name}: {compact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
