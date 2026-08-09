#!/usr/bin/env python3
"""Build new_posts_batch_v3.json — 60 social posts for Better Call Wes.

Mix is derived from 90 days of measured engagement:
  pillar:     personal 18 | trust 12 | local 10 | work 8 | emergency 5 | tips 5 | cost_reveal 2
  image_type: brand 26 | asset 19 | work 9 | review_card 6 | ai 0

Content lives in _v3_posts_a/b/c.py as plain dicts. This module expands them
into the full post shape (platform text, image prompts), validates, and writes.

Run:  python3 build_batch_v3.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _v3_posts_a import POSTS_A
from _v3_posts_b import POSTS_B
from _v3_posts_c import POSTS_C

OUT = os.path.join(HERE, "new_posts_batch_v3.json")

PHONE = "07700 155 655"
SHORT = "https://u.bettercallwes.co.uk/"

# --- service slug -> canonical service page --------------------------------

SERVICE_URL = {
    "boiler-repair": "https://bettercallwes.co.uk/services/boiler-repair.html",
    "boiler-service": "https://bettercallwes.co.uk/services/boiler-servicing.html",
    "boiler-install": "https://bettercallwes.co.uk/services/boiler-installation.html",
    "new-boiler": "https://bettercallwes.co.uk/services/boiler-installation.html",
    "combi-install": "https://bettercallwes.co.uk/services/boiler-installation.html",
    "power-flush": "https://bettercallwes.co.uk/services/power-flushing.html",
    "central-heating": "https://bettercallwes.co.uk/services/central-heating.html",
    "gas-safety": "https://bettercallwes.co.uk/services/gas-safety-check.html",
    "gas-leak": "https://bettercallwes.co.uk/services/gas-leak-detection.html",
    "cp12": "https://bettercallwes.co.uk/services/landlord-gas-safety-certificates.html",
    "plumbing": "https://bettercallwes.co.uk/services/plumbing-repairs.html",
    "radiators": "https://bettercallwes.co.uk/services/radiators.html",
    "smart-controls": "https://bettercallwes.co.uk/services/smart-controls.html",
    "heating-controls": "https://bettercallwes.co.uk/services/heating-controls.html",
    "toilet-repair": "https://bettercallwes.co.uk/services/toilet-repairs.html",
    "tap-repair": "https://bettercallwes.co.uk/services/tap-repair.html",
    "pipe-leak": "https://bettercallwes.co.uk/services/pipe-leak-repair.html",
    "shower-repair": "https://bettercallwes.co.uk/services/shower-repair.html",
    "system-flush": "https://bettercallwes.co.uk/services/system-flushing.html",
}

# --- SOURCE descriptions -----------------------------------------------------
# Each string must describe what the hinted image ACTUALLY shows, per
# image_catalogue.json. A hint can resolve to several files, so the description
# covers every file behind that hint.

WES_ID = (
    "Wes is a Black African British man with dark skin, wearing professional navy "
    "workwear. Keep his facial features, skin tone, expression, and uniform exactly "
    "as in the source."
)

SOURCE_DESC = {
    "asset:boiler": (
        "The input image shows a modern wall-mounted gas boiler in a UK home — a sealed "
        "white-cased unit with a small control display, clean copper pipework and "
        "isolation valves running below it, and a magnetic filter on the return pipe. "
        "No people are in frame."
    ),
    "asset:radiator": (
        "The input image shows a clean white panel radiator mounted on the wall of a cosy "
        "UK living room, with a sofa and knitted throw, a houseplant and framed botanical "
        "art nearby. No people are in frame."
    ),
    "asset:pipe": (
        "The input image shows a close-up of neat copper pipework — multiple junction "
        "fittings, a brass compression fitting, and a black magnetic filter on a tidy "
        "parallel pipe run against a plain wall. No people are in frame."
    ),
    "asset:gas": (
        "The input image shows a domestic gas meter installation — yellow gas pipe, an "
        "Elster BK-G4 meter, and brass isolation valves and taps. A clean equipment shot "
        "with no people in frame."
    ),
    "asset:heatex": (
        "The input image shows two Baxi heat exchangers side by side on a service mat — "
        "the left one clean with bright silver fins, the right one thick with black "
        "carbon and debris build-up. A genuine clean-versus-dirty pair. No people are in "
        "frame."
    ),
    "asset:van": (
        "The input image shows a black Ford Transit Custom SWB panel van parked on the "
        "driveway of a modern UK home with its side door open. Wide shot, no people in "
        "frame. This is the only van — do not substitute a different vehicle, colour or "
        "model."
    ),
    "asset:van_southampton": (
        "The input image is a Better Call Wes location shot — either the black Ford "
        "Transit Custom SWB panel van parked on a UK driveway with its side door open, or "
        "an aerial sunset view of the Southampton skyline showing the bridge over the "
        "Itchen, the marina and the river. No people in frame. If the van is present it is "
        "the only van — do not substitute a different vehicle, colour or model."
    ),
    "brand:wes_portrait": (
        "The input image is a real photograph of Wes standing outdoors in front of purple "
        "wisteria flowers, smiling, wearing a navy polo shirt with the Better Call Wes "
        "logo. " + WES_ID
    ),
    "brand:wes_with_tools": (
        "The input image shows Wes working hands-on at a heating or plumbing job inside a "
        "UK home — kneeling or crouching at a radiator, boiler, tap or flush rig, wearing "
        "a branded navy polo shirt, with his tools around him. " + WES_ID
    ),
    "brand:wes_with_phone": (
        "The input image shows Wes fitting a round smart thermostat to a wall while a "
        "second hand holds a phone displaying the heating app set to 18°C. Wes wears a "
        "branded navy polo shirt. " + WES_ID
    ),
    "work:install": (
        "The input image shows Wes mid-installation on a boiler job in a UK home — a new "
        "Worcester combi being positioned or already mounted, bare copper pipework, brass "
        "fittings and tools laid out on a dust sheet. Wes wears a navy polo shirt. " + WES_ID
    ),
    "work:boiler_repair": (
        "The input image shows Wes kneeling at a boiler in a utility cupboard with the "
        "control panel opened, holding a Fluke multimeter against the board, tools on the "
        "floor beside him. Wes wears a navy polo shirt. " + WES_ID
    ),
    "work:powerflush": (
        "The input image shows Wes mid power-flush in a branded navy polo — either "
        "kneeling beside a black Kamco power-flush rig holding an orange flush hose "
        "connected to the boiler with an ADEY MagnaClean filter visible, or wearing blue "
        "gloves and pouring jet-black sludge water out of a MagnaClean filter into a clear "
        "bucket. " + WES_ID
    ),
    "work:radiator_swap": (
        "The input image shows Wes kneeling in a hallway, using a screwdriver on a white "
        "panel radiator, wearing a branded navy polo shirt. " + WES_ID
    ),
    "work:pipe_repair": (
        "The input image shows Wes kneeling or lying under a kitchen sink with a torch and "
        "a wrench, working on the waste pipework, with a towel laid down to catch spills. "
        "Wes wears a navy polo shirt. " + WES_ID
    ),
    "work:toilet_repair": (
        "The input image shows Wes in a bathroom with the toilet cistern lid removed, "
        "holding a brass flush mechanism, replacement parts laid out on the cistern and a "
        "tool bag on the floor. Wes wears a navy polo shirt. " + WES_ID
    ),
    "work:tap_install": (
        "The input image shows Wes in a kitchen mid tap job — holding a blue tap cartridge "
        "with the replacement in its packaging on the worktop, or reaching up under the "
        "sink to fit a chrome mixer tap from below. Wes wears a navy polo shirt. " + WES_ID
    ),
    "work:shower": (
        "The input image shows Wes in a tiled bathroom working on a shower — holding a "
        "thermostatic shower cartridge beside an opened recessed shower valve, or using a "
        "yellow spirit level to align a shower riser rail. Wes wears a navy polo shirt. "
        + WES_ID
    ),
    "work:gas_inspection": (
        "The input image shows Wes carrying out a gas inspection — either outdoors at an "
        "external gas meter cabinet holding a clipboard, or kneeling at a kitchen gas hob "
        "using a handheld electronic gas leak detector with an LED probe. Wes wears a navy "
        "polo shirt. " + WES_ID
    ),
}

BANNER = (
    "- Banner style: solid rectangle, brand navy #0A2540, 88% opacity, full-width, 14% of "
    "image height, clean edges\n"
    "- Small orange #FF6B00 accent bar, 4px, along the top edge of the banner\n"
    '- Headline (EXACT TEXT, verbatim, no substitutions, no duplicates): "{caption}"\n'
    "- Typography: bold sans-serif, white, centred, generous kerning, optically sized for "
    "social-feed legibility"
)


def overlay_prompt(hint, caption, position="lower third"):
    """Image-to-image caption-banner prompt for brand / work / asset sources."""
    return (
        "TASK: Add a caption banner overlay to the source photo.\n\n"
        "SOURCE: {src} Preserve the following exactly: subject, hardware, pipework, "
        "valves, labels, wall texture, lighting direction, shadows, camera angle, crop, "
        "and colour grade. Do NOT add, remove, or alter any hardware, fittings, tools, or "
        "background elements beyond those already present.\n\n"
        "CHANGE: Add ONE caption banner in the {pos}.\n{banner}\n\n"
        "CONSTRAINTS: Render the headline verbatim. No extra words. No ghosted or "
        "duplicate text. No watermark. No logo. Keep everything outside the banner "
        "pixel-identical to the source.\n\n"
        "USE CASE: Instagram social post, square 1:1, 1080x1080."
    ).format(src=SOURCE_DESC[hint], pos=position, banner=BANNER.format(caption=caption))


def mascot_prompt(scene, caption):
    """Mascot-on-landmark prompt for the 'Where's Wes today?' series."""
    return (
        "TASK: Place the cartoon mascot character from the source image into a new "
        "scene.\n\n"
        "SOURCE: The input image is the Better Call Wes logo featuring a cartoon mascot of "
        "a Black African plumber in a navy polo holding a wrench and phone. Preserve the "
        "mascot's exact appearance, style, colours and proportions.\n\n"
        "SCENE: {scene}, with the cartoon mascot standing playfully in the foreground "
        "giving a thumbs up — deliberate cartoon-on-photo contrast, like a mascot sticker "
        "on a postcard.\n\n"
        "CHANGE: Add ONE caption banner in the lower third.\n{banner}\n\n"
        "CONSTRAINTS: Render the headline verbatim. No other text. Keep the mascot's "
        "identity exact. No watermark.\n\n"
        "USE CASE: Instagram social post, square 1:1, 1080x1080."
    ).format(scene=scene, banner=BANNER.format(caption=caption))


BASE_TAGS = [
    "#Southampton", "#SO14", "#SO15", "#SO16", "#SO17",
    "#Plumber", "#GasSafe", "#GasSafeEngineer", "#HeatingEngineer",
    "#SouthamptonPlumber",
]


def expand(raw, index):
    """Turn a compact content dict into a full post object."""
    slug = raw["slug"]
    link = SHORT + slug
    hint = raw["ihint"]

    facebook = raw["fb"].strip() + "\n\n{}\nCall/WhatsApp Wes: {}".format(link, PHONE)

    tags = list(raw.get("ig_tags", [])) + BASE_TAGS
    instagram = (
        raw["ig"].strip()
        + "\n\n🔗 Link in bio\n\n"
        + " ".join(tags)
    )

    twitter = raw["tw"].strip().replace("{L}", link)
    googlebusiness = raw["gb"].strip() + "\n\n{}\nCall/WhatsApp: {}".format(link, PHONE)

    if raw["itype"] == "review_card":
        prompt = ""
    elif hint == "asset:logo_mascot":
        prompt = mascot_prompt(raw["scene"], raw["caption"])
    else:
        prompt = overlay_prompt(hint, raw["caption"], raw.get("pos", "lower third"))

    post = {
        "id": "post_{:03d}".format(index),
        "pillar": raw["pillar"],
        "topic": raw["topic"],
        "service_url": SERVICE_URL[slug],
        "service_slug": slug,
        "short_link_slug": raw["link"],
        "facebook": facebook,
        "instagram": instagram,
        "twitter": twitter,
        "googlebusiness": googlebusiness,
        "image_type": raw["itype"],
        "image_hint": hint,
        "caption": raw["caption"],
        "image_prompt": prompt,
    }
    if "prerendered" in raw:
        post["prerendered_image"] = raw["prerendered"]
    return post


# --- validation --------------------------------------------------------------

VALID_HINTS = {
    "asset:boiler", "asset:radiator", "asset:tap", "asset:pipe", "asset:gas",
    "asset:shower", "asset:smart", "asset:plumbing", "asset:van_southampton",
    "asset:heatex", "asset:tools", "asset:van", "asset:logo_mascot",
    "work:install", "work:powerflush", "work:tap_install", "work:radiator_swap",
    "work:pipe_repair", "work:boiler_repair", "work:shower", "work:toilet_repair",
    "work:tank_service", "work:gas_inspection", "work:smart_install", "work:manifold",
    "brand:wes_portrait", "brand:wes_with_tools", "brand:wes_with_phone",
    "review_card",
}

PILLAR_TARGET = {
    "personal": 18, "trust": 12, "local": 10, "work": 8,
    "emergency": 5, "tips": 5, "cost_reveal": 2,
}

REVIEW_CARDS = [
    "review_cards/review-03-elaine.png",
    "review_cards/review-04-james.png",
    "review_cards/review-05-jack.png",
    "review_cards/review-06-mikey.png",
    "review_cards/review-07-sam.png",
    "review_cards/review-08-tracey.png",
]

FORBIDDEN = ["no vat", " vat ", "vat-free", "558654", "before vs after", "before and after"]


def validate(posts):
    errs = []

    if len(posts) != 60:
        errs.append("expected 60 posts, got {}".format(len(posts)))

    # pillar counts
    counts = {}
    for p in posts:
        counts[p["pillar"]] = counts.get(p["pillar"], 0) + 1
    for pillar, want in PILLAR_TARGET.items():
        if counts.get(pillar, 0) != want:
            errs.append("pillar {}: want {}, got {}".format(pillar, want, counts.get(pillar, 0)))

    # slugs
    slugs = [p["short_link_slug"] for p in posts]
    if len(set(slugs)) != len(slugs):
        dupes = sorted({s for s in slugs if slugs.count(s) > 1})
        errs.append("duplicate short_link_slug: {}".format(dupes))
    for s in slugs:
        try:
            n = int(s[1:4])
        except ValueError:
            errs.append("bad slug format: {}".format(s))
            continue
        if not s.startswith("p") or not (151 <= n <= 210):
            errs.append("slug out of p151-p210 range: {}".format(s))

    ids = [p["id"] for p in posts]
    if len(set(ids)) != len(ids):
        errs.append("duplicate ids")

    topics = [p["topic"] for p in posts]
    if len(set(topics)) != len(topics):
        errs.append("duplicate topics: {}".format(sorted({t for t in topics if topics.count(t) > 1})))

    for p in posts:
        pid = p["id"]

        if p["image_hint"] not in VALID_HINTS:
            errs.append("{}: invalid image_hint {!r}".format(pid, p["image_hint"]))

        if p["image_type"] == "ai":
            errs.append("{}: image_type 'ai' is banned".format(pid))

        if len(p["twitter"]) > 260:
            errs.append("{}: twitter {} chars (>260)".format(pid, len(p["twitter"])))

        if "#" in p["facebook"]:
            errs.append("{}: facebook contains a hashtag".format(pid))

        if "https://" in p["instagram"].split("🔗 Link in bio")[0]:
            errs.append("{}: instagram body contains https://".format(pid))

        if "#" in p["googlebusiness"]:
            errs.append("{}: googlebusiness contains a hashtag".format(pid))

        if len(p["caption"].split()) > 8:
            errs.append("{}: caption >8 words: {!r}".format(pid, p["caption"]))

        # before/after promise in caption only allowed on the genuine pair image
        if p["image_hint"] != "asset:heatex":
            low = p["caption"].lower()
            if "→" in p["caption"] or "before vs after" in low or " vs " in low:
                errs.append("{}: before/after caption without a pair image".format(pid))

        blob = " ".join([p["facebook"], p["instagram"], p["twitter"],
                         p["googlebusiness"], p["caption"], p["topic"]]).lower()
        for bad in FORBIDDEN:
            if bad in blob:
                errs.append("{}: forbidden phrase {!r}".format(pid, bad))

        # every post links to its service via the short link
        want = SHORT + p["service_slug"]
        for field in ("facebook", "twitter", "googlebusiness"):
            if want not in p[field]:
                errs.append("{}: {} missing short link {}".format(pid, field, want))

        if p["image_type"] != "review_card" and not p["image_prompt"].strip():
            errs.append("{}: empty image_prompt".format(pid))

        gb_words = len(p["googlebusiness"].split())
        if not (95 <= gb_words <= 165):
            errs.append("{}: googlebusiness {} words (want ~100-150)".format(pid, gb_words))

    # review cards
    rc = [p for p in posts if p["image_type"] == "review_card"]
    if len(rc) != 6:
        errs.append("expected 6 review_card posts, got {}".format(len(rc)))
    got = [p.get("prerendered_image") for p in rc]
    if sorted(got) != sorted(REVIEW_CARDS):
        errs.append("review card paths mismatch: {}".format(got))
    for p in rc:
        if p["image_hint"] != "review_card":
            errs.append("{}: review_card post needs image_hint 'review_card'".format(p["id"]))
        if p["image_prompt"] != "":
            errs.append("{}: review_card image_prompt must be empty".format(p["id"]))
        path = os.path.join(HERE, p["prerendered_image"])
        if not os.path.exists(path):
            errs.append("{}: missing card file {}".format(p["id"], p["prerendered_image"]))

    # mascot landmark posts
    mascot = [p for p in posts if p["image_hint"] == "asset:logo_mascot"]
    if len(mascot) != 4:
        errs.append("expected 4 mascot landmark posts, got {}".format(len(mascot)))

    return errs


def main():
    raw = POSTS_A + POSTS_B + POSTS_C
    posts = [expand(r, i + 1) for i, r in enumerate(raw)]

    errs = validate(posts)

    itypes = {}
    for p in posts:
        itypes[p["image_type"]] = itypes.get(p["image_type"], 0) + 1
    pillars = {}
    for p in posts:
        pillars[p["pillar"]] = pillars.get(p["pillar"], 0) + 1

    print("posts:      {}".format(len(posts)))
    print("pillars:    {}".format(dict(sorted(pillars.items()))))
    print("image_type: {}".format(dict(sorted(itypes.items()))))
    longest = max(posts, key=lambda p: len(p["twitter"]))
    print("longest tweet: {} chars ({})".format(len(longest["twitter"]), longest["id"]))
    print("review cards at: {}".format(
        [p["id"] for p in posts if p["image_type"] == "review_card"]))
    print("mascot posts at: {}".format(
        [p["id"] for p in posts if p["image_hint"] == "asset:logo_mascot"]))

    if errs:
        print("\nVALIDATION FAILED ({} issues):".format(len(errs)))
        for e in errs:
            print("  ✗ {}".format(e))
        sys.exit(1)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(posts, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print("\nVALIDATION PASSED — wrote {}".format(OUT))


if __name__ == "__main__":
    main()
