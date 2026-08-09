#!/usr/bin/env python3
"""Build the 60-post social batch (p091-p150) for Better Call Wes.

Composes platform texts from content entries in _batch60_posts_{a,b,c}.py,
generates structured GPT Image 2 prompts per SKILL.md, validates everything,
and writes new_posts_batch_60.json.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _batch60_posts_a import POSTS_A
from _batch60_posts_b import POSTS_B
from _batch60_posts_c import POSTS_C

HERE = Path(__file__).parent
OUT = HERE / "new_posts_batch_60.json"

PHONE = "07700 155 655"
SHORT = "https://u.bettercallwes.co.uk/"

# short-link slug -> service page
PAGE_MAP = {
    "boiler-repair": "boiler-repair.html",
    "boiler-service": "boiler-servicing.html",
    "boiler-install": "boiler-installation.html",
    "new-boiler": "boiler-installation.html",
    "combi-install": "boiler-installation.html",
    "power-flush": "power-flushing.html",
    "central-heating": "central-heating.html",
    "gas-safety": "gas-safety-check.html",
    "gas-leak": "gas-leak-detection.html",
    "cp12": "landlord-gas-safety-certificates.html",
    "plumbing": "plumbing-repairs.html",
    "radiators": "radiators.html",
    "smart-controls": "smart-controls.html",
    "heating-controls": "heating-controls.html",
    "toilet-repair": "toilet-repairs.html",
    "tap-repair": "tap-repair.html",
    "pipe-leak": "pipe-leak-repair.html",
    "shower-repair": "shower-repair.html",
    "system-flush": "system-flushing.html",
}

ALLOWED_HINTS = {
    "asset:boiler", "asset:radiator", "asset:tap", "asset:pipe", "asset:gas",
    "asset:shower", "asset:smart", "asset:plumbing", "asset:van",
    "asset:van_southampton", "asset:heatex", "asset:tools", "asset:logo_mascot",
    "work:install", "work:powerflush", "work:tap_install", "work:radiator_swap",
    "work:pipe_repair", "work:boiler_repair", "work:shower", "work:toilet_repair",
    "work:tank_service", "work:gas_inspection", "work:smart_install",
    "work:manifold", "brand:wes_portrait", "brand:wes_with_tools",
    "brand:wes_with_phone", "review_card", "ai",
}

CTA_TEXT = {
    "QUOTE": "Comment QUOTE and I'll DM you my booking link.",
    "SERVICE": "Comment SERVICE and I'll DM you my service-booking link.",
    "SLUDGE": "Comment SLUDGE and I'll DM you the power-flush deal.",
}

LOCAL_TAGS = ["#Southampton", "#SO14", "#SO15", "#SO16", "#SO17"]
TRADE_TAGS = ["#Plumber", "#GasSafe", "#GasSafeEngineer", "#HeatingEngineer", "#SouthamptonPlumber"]

WES_LINE = ("Wes is a Black African British man with dark skin, wearing professional "
            "navy workwear. Keep his facial features, skin tone, expression, and "
            "uniform exactly as in the source.")

# SOURCE descriptions aligned with image_catalogue.json per hint. (desc, shows_wes)
SRC = {
    "asset:boiler": ("a modern wall-mounted combi boiler in a UK home — a sealed white unit with a small digital display, clean copper pipework running below it and a magnetic filter on the return pipe", False),
    "asset:radiator": ("a clean white panel radiator mounted on the wall of a cosy UK living room, with a sofa draped in a knitted throw, a houseplant and framed botanical art nearby", False),
    "asset:tap": ("a clean chrome mixer tap over a white kitchen sink in a bright UK kitchen, a garden visible through the window behind", False),
    "asset:pipe": ("a close-up of neat copper pipework with multiple junction fittings and a brass compression fitting against a neutral wall", False),
    "asset:gas": ("a domestic gas meter installation with yellow gas pipes, a grey meter unit, brass valves and isolation taps, clean and well maintained", False),
    "asset:shower": ("a modern walk-in shower with a rain head running water, a glass screen, white subway tiles and a white sink unit", False),
    "asset:smart": ("a round smart thermostat being fitted to a hallway wall by Wes while a customer's hand holds a phone showing the heating app set to 18°C", True),
    "asset:plumbing": ("a clean chrome mixer tap running water into a white kitchen sink in a bright UK kitchen", False),
    "asset:van": ("a black Ford Transit Custom SWB panel van parked on the driveway of a modern UK home with its side door open, no people in frame", False),
    "asset:van_southampton": ("a black Ford Transit Custom SWB panel van parked on the driveway of a modern UK home with its side door open, no people in frame", False),
    "asset:heatex": ("two boiler heat exchangers side by side on a service mat — the left one clean with bright silver fins, the right one clogged with dark carbon and debris build-up", False),
    "asset:tools": ("a plumber's tools laid flat on a wooden surface — a multimeter, adjustable wrench, pipe cutter, copper elbow fittings, a pipe bender and PTFE tape", False),
    "work:install": ("Wes lifting a new white combi boiler into position on a bare wall, packaging on the floor below him", True),
    "work:powerflush": ("Wes kneeling beside a black power-flush rig connected to a heating system by an orange flush hose, a magnetic filter visible, mid-flush", True),
    "work:tap_install": ("Wes in a kitchen holding a worn tap cartridge, with the new replacement cartridge in its packaging on the worktop beside him", True),
    "work:radiator_swap": ("Wes kneeling in a hallway using a screwdriver on a white panel radiator", True),
    "work:pipe_repair": ("Wes under a kitchen sink holding a torch and a wrench, looking up and inspecting the waste pipework above him", True),
    "work:boiler_repair": ("Wes kneeling in a utility cupboard holding a multimeter probe against the opened control panel of a wall-mounted boiler, tools on the floor beside him", True),
    "work:shower": ("Wes in a tiled bathroom holding a thermostatic shower cartridge, examining a recessed shower valve in the wall", True),
    "work:toilet_repair": ("Wes holding a brass flush mechanism removed from a toilet cistern, with replacement parts laid out on the cistern lid", True),
    "work:tank_service": ("Wes standing beside an unvented hot water cylinder in an airing cupboard, holding a pressure gauge connected to the cylinder", True),
    "work:gas_inspection": ("Wes kneeling next to a gas hob in a kitchen, using an electronic gas leak detector with an LED probe, focused on the appliance", True),
    "work:smart_install": ("Wes in a hallway using a screwdriver to fit a round thermostat dial to the wall", True),
    "work:manifold": ("a tidy run of parallel copper pipes against a wall with a black magnetic filter mounted on the pipework, floorboards lifted to show the workmanship", False),
    "brand:wes_portrait": ("Wes standing outdoors in front of purple wisteria flowers, smiling at the camera, wearing a navy polo shirt with the Better Call Wes logo", True),
    "brand:wes_with_tools": ("Wes kneeling and working hands-on at a heating job with tools around him, wearing a navy branded polo shirt", True),
    "brand:wes_with_phone": ("Wes fitting a smart thermostat to a wall while a customer's hand holds a phone showing the heating app", True),
}


def overlay_prompt(hint, caption, banner):
    desc, has_wes = SRC[hint]
    wes = (" " + WES_LINE) if has_wes else ""
    third = "upper third" if banner == "upper" else "lower third"
    return (
        "TASK: Add a caption banner overlay to the source photo.\n\n"
        f"SOURCE: The input image shows {desc}.{wes} Preserve the following exactly: "
        "subject, hardware, pipework, valves, labels, wall texture, lighting direction, "
        "shadows, camera angle, crop, and colour grade. Do NOT add, remove, or alter any "
        "hardware, fittings, tools, or background elements beyond those already present.\n\n"
        f"CHANGE: Add ONE caption banner in the {third}.\n"
        "- Banner style: solid rectangle, brand navy #0A2540, 88% opacity, full-width, "
        "14% of image height, clean edges\n"
        "- Small orange #FF6B00 accent bar, 4px, along the top edge of the banner\n"
        f"- Headline (EXACT TEXT, verbatim, no substitutions, no duplicates): \"{caption}\"\n"
        "- Typography: bold sans-serif, white, centred, generous kerning, optically sized "
        "for social-feed legibility\n\n"
        "CONSTRAINTS: Render the headline verbatim. No extra words. No ghosted or duplicate "
        "text. No watermark. No logo. Keep everything outside the banner pixel-identical "
        "to the source.\n\n"
        "USE CASE: Instagram social post, square 1:1, 1080x1080."
    )


def compose(posts):
    out = []
    for i, p in enumerate(posts):
        n = 91 + i
        slug = p["slug"]
        url = SHORT + slug
        cta = CTA_TEXT.get(p["cta"]) if p.get("cta") else None
        extra = p.get("extra_cta")

        # Facebook: body + CTA(s) + short link + phone. No hashtags.
        fb_parts = [p["fb"]]
        if cta:
            fb_parts.append(cta)
        if extra:
            fb_parts.append(extra)
        fb_parts.append(url + "\nCall/WhatsApp Wes: " + PHONE)
        facebook = "\n\n".join(fb_parts)

        # Instagram: body + CTA(s) + Link in bio + 12-15 hashtags. No URLs.
        tags = list(p["tags"]) + LOCAL_TAGS + TRADE_TAGS
        ig_parts = [p["ig"]]
        if cta:
            ig_parts.append(cta)
        if extra:
            ig_parts.append(extra)
        ig_parts.append("🔗 Link in bio")
        ig_parts.append(" ".join(tags))
        instagram = "\n\n".join(ig_parts)

        # Twitter: body + short link + 1 hashtag, <=260 chars.
        twitter = p["tw"] + "\n\n" + url + " #Southampton"

        # Google Business: body + short link + phone. No hashtags.
        googlebusiness = p["gb"] + "\n\n" + url + "\nCall/WhatsApp: " + PHONE

        # Image prompt
        if "prompt" in p and p["prompt"] is not None:
            prompt = p["prompt"]
        else:
            prompt = overlay_prompt(p["hint"], p["caption"], p["banner"])

        post = {
            "id": f"post_{i + 1:03d}",
            "pillar": p["pillar"],
            "topic": p["topic"],
            "service_url": "https://bettercallwes.co.uk/services/" + PAGE_MAP[slug],
            "service_slug": slug,
            "short_link_slug": f"p{n:03d}-{p['suffix']}",
            "facebook": facebook,
            "instagram": instagram,
            "twitter": twitter,
            "googlebusiness": googlebusiness,
            "image_type": p["itype"],
            "image_hint": p["hint"],
            "caption": p["caption"],
            "image_prompt": prompt,
        }
        if p.get("prerendered"):
            post["prerendered_image"] = p["prerendered"]
        out.append(post)
    return out


def validate(posts):
    errors, warnings = [], []

    if len(posts) != 60:
        errors.append(f"Expected 60 posts, got {len(posts)}")

    # Pillar counts (local includes the 4 mascot posts)
    expected = {"cost_reveal": 12, "tips": 10, "personal": 9, "work": 8,
                "local": 11, "trust": 5, "emergency": 5}
    counts = {}
    for p in posts:
        counts[p["pillar"]] = counts.get(p["pillar"], 0) + 1
    if counts != expected:
        errors.append(f"Pillar counts wrong: {counts} != {expected}")

    # Slug numbering/uniqueness p091-p150
    slugs = [p["short_link_slug"] for p in posts]
    if len(set(slugs)) != len(slugs):
        errors.append("Duplicate short_link_slugs")
    for i, s in enumerate(slugs):
        want = f"p{91 + i:03d}-"
        if not s.startswith(want):
            errors.append(f"{posts[i]['id']}: slug {s!r} should start {want!r}")
        if not re.fullmatch(r"p\d{3}-[a-z0-9-]+", s):
            errors.append(f"{posts[i]['id']}: slug {s!r} malformed")

    vat_re = re.compile(r"\bvat\b", re.IGNORECASE)
    avail_re = re.compile(r"always (answer|pick|respond)", re.IGNORECASE)

    review_positions = []
    for idx, p in enumerate(posts):
        pid = p["id"]
        texts = {f: p[f] for f in ("facebook", "instagram", "twitter", "googlebusiness",
                                   "caption", "topic", "image_prompt")}

        # Forbidden phrases everywhere
        for f, t in texts.items():
            if vat_re.search(t):
                errors.append(f"{pid}.{f}: mentions VAT")
            if "558654" in t:
                errors.append(f"{pid}.{f}: contains Gas Safe number")
            if avail_re.search(t):
                errors.append(f"{pid}.{f}: implies Wes always answers")

        # Platform rules
        if "#" in p["facebook"]:
            errors.append(f"{pid}: facebook contains '#'")
        if "https://" in p["instagram"] or "http://" in p["instagram"]:
            errors.append(f"{pid}: instagram contains a URL")
        if "🔗 Link in bio" not in p["instagram"]:
            errors.append(f"{pid}: instagram missing 'Link in bio'")
        n_tags = len(re.findall(r"#\w+", p["instagram"]))
        if not 12 <= n_tags <= 15:
            errors.append(f"{pid}: instagram has {n_tags} hashtags (need 12-15)")
        if len(p["twitter"]) > 260:
            errors.append(f"{pid}: twitter is {len(p['twitter'])} chars (max 260)")

        # Short link presence
        short = SHORT + p["service_slug"]
        for f in ("facebook", "twitter", "googlebusiness"):
            if short not in p[f]:
                errors.append(f"{pid}.{f}: missing short link {short}")
        if p["service_slug"] not in PAGE_MAP:
            errors.append(f"{pid}: bad service_slug {p['service_slug']}")
        if not p["service_url"].endswith(PAGE_MAP[p["service_slug"]]):
            errors.append(f"{pid}: service_url/slug mismatch")

        # Image rules
        if p["image_hint"] not in ALLOWED_HINTS:
            errors.append(f"{pid}: image_hint {p['image_hint']!r} not allowed")
        if p["image_type"] == "review_card":
            review_positions.append(idx + 1)
            if not p.get("prerendered_image"):
                errors.append(f"{pid}: review_card missing prerendered_image")
        # Caption rules
        words = [w for w in p["caption"].split() if w]
        if len(words) > 8:
            errors.append(f"{pid}: caption {len(words)} words (max 8): {p['caption']!r}")
        cap_low = p["caption"].lower()
        if p["image_hint"] != "asset:heatex" and ("→" in p["caption"] or "before" in cap_low):
            errors.append(f"{pid}: before/after caption without heatex pair: {p['caption']!r}")

        # GB word count (soft)
        gb_words = len(p["googlebusiness"].split())
        if not 90 <= gb_words <= 165:
            warnings.append(f"{pid}: googlebusiness {gb_words} words (target 100-150)")

    if len(review_positions) != 2:
        errors.append(f"Expected exactly 2 review_card posts, got {review_positions}")
    else:
        a, b = review_positions
        if not (8 <= a <= 12 and 38 <= b <= 42):
            errors.append(f"review_card positions {review_positions} not near 10 and 40")

    # CTA keyword sanity: SLUDGE only on flush/heating-system posts
    for p in posts:
        if "Comment SLUDGE" in p["facebook"]:
            if p["service_slug"] not in {"power-flush", "system-flush", "central-heating"}:
                errors.append(f"{p['id']}: SLUDGE keyword on slug {p['service_slug']}")

    return errors, warnings


def main():
    posts = compose(POSTS_A + POSTS_B + POSTS_C)
    errors, warnings = validate(posts)

    for w in warnings:
        print("WARN:", w)
    if errors:
        for e in errors:
            print("FAIL:", e)
        sys.exit(1)

    OUT.write_text(json.dumps(posts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Report
    pillars, itypes, hints = {}, {}, {}
    for p in posts:
        pillars[p["pillar"]] = pillars.get(p["pillar"], 0) + 1
        itypes[p["image_type"]] = itypes.get(p["image_type"], 0) + 1
        hints[p["image_hint"]] = hints.get(p["image_hint"], 0) + 1
    longest = max(posts, key=lambda p: len(p["twitter"]))
    print(f"OK: wrote {len(posts)} posts -> {OUT}")
    print("Pillars:", dict(sorted(pillars.items(), key=lambda x: -x[1])))
    print("Image types:", dict(sorted(itypes.items(), key=lambda x: -x[1])))
    print("Hints:", dict(sorted(hints.items(), key=lambda x: -x[1])))
    print(f"Longest tweet: {len(longest['twitter'])} chars ({longest['id']}, {longest['short_link_slug']})")
    rc = [p["id"] for p in posts if p["image_type"] == "review_card"]
    print("Review cards at:", rc)


if __name__ == "__main__":
    main()
