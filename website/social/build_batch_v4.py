#!/usr/bin/env python3
"""Build new_posts_batch_v4.json — 60 social posts for Better Call Wes.

Mix is derived from 150 days of measured engagement across two independent
measurement periods. Personal content + Wes-in-frame imagery is the only
reliable winner, so it is now half the batch:

  pillar:     personal 30 | local 8 | tips 6 | work 6 | emergency 4 | trust 4 | cost_reveal 2
  image_type: brand 32 | asset 16 | work 10 | review_card 2 | ai 0

Seasonal angle: early August heading into autumn. Sept–Oct is Southampton's
boiler-service booking season, so tips / emergency / trust / cost_reveal lean
"get it sorted before the rush". Personal posts stay evergreen (reach driver).

Timing: cron posts 08:07 / 13:07 / 18:07 in array order. 13:07 is the best slot
(1.88 eng/post) so every array index ≡ 1 (mod 3) carries a strong personal post.

Content lives in _v4_posts_a/b/c.py as plain dicts. This module expands them
into the full post shape (platform text, image prompts), validates, and writes.

Run:  python3 build_batch_v4.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _v4_posts_a import POSTS_A
from _v4_posts_b import POSTS_B
from _v4_posts_c import POSTS_C

OUT = os.path.join(HERE, "new_posts_batch_v4.json")
PREV = os.path.join(HERE, "new_posts_batch_v3.json")

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
        "The input image shows a modern wall-mounted gas combi boiler in a UK home — a "
        "sealed white-cased unit with a small digital display, clean copper pipework and "
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
    "asset:tools": (
        "The input image is a clean overhead flat-lay of a plumber's tools on a wooden "
        "surface — a Fluke multimeter, an adjustable wrench, a Ridgid pipe cutter, copper "
        "elbow fittings, a pipe bender and a roll of PTFE tape. No people are in frame."
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
        "The input image shows Wes kneeling under a kitchen sink with a torch and a "
        "wrench, looking up at the waste pipework mid-inspection. Wes wears a navy polo "
        "shirt. " + WES_ID
    ),
    "work:tap_install": (
        "The input image shows Wes in a kitchen mid tap job — holding a blue tap cartridge "
        "with the replacement cartridge still in its packaging on the worktop. Wes wears a "
        "navy polo shirt. " + WES_ID
    ),
    "work:smart_install": (
        "The input image shows Wes in a hallway using a screwdriver on a round Nest-style "
        "thermostat dial mounted on the wall, mid-install. Wes wears a navy polo shirt. "
        + WES_ID
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
        "a Black African plumber in a navy polo holding an adjustable wrench and a phone, "
        "set on an orange circle. Preserve the mascot's exact appearance, style, colours "
        "and proportions. Ignore the wordmark — do not reproduce any logo text.\n\n"
        "SCENE: {scene}, with the cartoon mascot standing playfully in the foreground "
        "giving a thumbs up — deliberate cartoon-on-photo contrast, like a mascot sticker "
        "on a postcard.\n\n"
        "CHANGE: Add ONE caption banner in the lower third.\n{banner}\n\n"
        "CONSTRAINTS: Render the headline verbatim. No other text. Keep the mascot's "
        "identity exact. No watermark. No fake logos.\n\n"
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
    instagram = raw["ig"].strip() + "\n\n🔗 Link in bio\n\n" + " ".join(tags)

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
    "personal": 30, "local": 8, "tips": 6, "work": 6,
    "emergency": 4, "trust": 4, "cost_reveal": 2,
}

IMAGE_TYPE_TARGET = {"brand": 32, "asset": 16, "work": 10, "review_card": 2}

REVIEW_CARDS = {
    "review_cards/review-03-elaine.png",
    "review_cards/review-08-tracey.png",
}

FORBIDDEN = [
    "no vat", " vat ", " vat.", "vat-free", "558654",
    "before vs after", "before and after", "deducted from",
    "comes off the repair", "knocked off the repair",
]

# same-day / weekend language rules
SAMEDAY = ["same day", "same-day", "sorted today", "out today", "fixed today",
           "fix it today", "here today", "there today", "tonight", "right now"]
WEEKEND = ["weekend", "saturday", "sunday"]

CTA_KEYWORDS = [
    "Comment QUOTE and I'll DM you my booking link",
    "Comment SERVICE and I'll DM you my service-booking link",
    "Comment SLUDGE and I'll DM you the power-flush deal",
]


def validate(posts):
    errs = []

    if len(posts) != 60:
        errs.append("expected 60 posts, got {}".format(len(posts)))

    counts = {}
    itypes = {}
    for p in posts:
        counts[p["pillar"]] = counts.get(p["pillar"], 0) + 1
        itypes[p["image_type"]] = itypes.get(p["image_type"], 0) + 1

    for pillar, want in PILLAR_TARGET.items():
        if counts.get(pillar, 0) != want:
            errs.append("pillar {}: want {}, got {}".format(pillar, want, counts.get(pillar, 0)))
    for extra in set(counts) - set(PILLAR_TARGET):
        errs.append("unexpected pillar {!r}".format(extra))

    for it, want in IMAGE_TYPE_TARGET.items():
        if itypes.get(it, 0) != want:
            errs.append("image_type {}: want {}, got {}".format(it, want, itypes.get(it, 0)))
    if itypes.get("ai"):
        errs.append("image_type 'ai' used {} times — banned".format(itypes["ai"]))

    # slugs p211–p270, unique
    slugs = [p["short_link_slug"] for p in posts]
    if len(set(slugs)) != len(slugs):
        dupes = sorted({s for s in slugs if slugs.count(s) > 1})
        errs.append("duplicate short_link_slug: {}".format(dupes))
    for s in slugs:
        if not s.startswith("p"):
            errs.append("bad slug format: {}".format(s))
            continue
        try:
            n = int(s[1:4])
        except ValueError:
            errs.append("bad slug format: {}".format(s))
            continue
        if not (211 <= n <= 270):
            errs.append("slug out of p211-p270 range: {}".format(s))

    ids = [p["id"] for p in posts]
    if len(set(ids)) != len(ids):
        errs.append("duplicate ids")

    topics = [p["topic"] for p in posts]
    if len(set(topics)) != len(topics):
        errs.append("duplicate topics: {}".format(
            sorted({t for t in topics if topics.count(t) > 1})))

    # no repeated topics from the previous batch
    if os.path.exists(PREV):
        with open(PREV, encoding="utf-8") as fh:
            prev_topics = {q["topic"].strip().lower() for q in json.load(fh)}
        for t in topics:
            if t.strip().lower() in prev_topics:
                errs.append("topic repeated from v3: {!r}".format(t))

    # 13:07 slot discipline — indices ≡ 1 (mod 3) must be personal
    for i, p in enumerate(posts):
        if i % 3 == 1 and p["pillar"] != "personal":
            errs.append("{} (index {}, 13:07 slot) is {!r}, must be personal".format(
                p["id"], i, p["pillar"]))

    for p in posts:
        pid = p["id"]

        if p["image_hint"] not in VALID_HINTS:
            errs.append("{}: invalid image_hint {!r}".format(pid, p["image_hint"]))

        if len(p["twitter"]) > 260:
            errs.append("{}: twitter {} chars (>260)".format(pid, len(p["twitter"])))

        if "#" in p["facebook"]:
            errs.append("{}: facebook contains a hashtag".format(pid))

        if "https://" in p["instagram"].split("🔗 Link in bio")[0]:
            errs.append("{}: instagram body contains https://".format(pid))

        if "#" in p["googlebusiness"]:
            errs.append("{}: googlebusiness contains a hashtag".format(pid))

        ig_tags = [w for w in p["instagram"].split() if w.startswith("#")]
        if not (12 <= len(ig_tags) <= 15):
            errs.append("{}: instagram has {} hashtags (want 12-15)".format(pid, len(ig_tags)))

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

        # availability language
        scrubbed = blob.replace("wes today", "")
        if p["pillar"] != "emergency":
            for phrase in SAMEDAY:
                if phrase in scrubbed:
                    errs.append("{}: same-day language {!r} on non-emergency post".format(
                        pid, phrase))
        for phrase in WEEKEND:
            if phrase in scrubbed:
                errs.append("{}: weekend availability language {!r}".format(pid, phrase))

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

        fb_words = len(p["facebook"].split())
        if not (60 <= fb_words <= 230):
            errs.append("{}: facebook {} words (want 60-230)".format(pid, fb_words))

    # CTA keywords — only the three approved ones may appear
    for p in posts:
        for field in ("facebook", "instagram"):
            txt = p[field]
            if "Comment " in txt:
                if not any(k in txt for k in CTA_KEYWORDS):
                    errs.append("{}: non-standard Comment CTA in {}".format(p["id"], field))
                if "SLUDGE" in txt and p["service_slug"] not in (
                        "power-flush", "system-flush", "central-heating"):
                    errs.append("{}: SLUDGE CTA on non-flush topic".format(p["id"]))

    # review cards
    rc = [p for p in posts if p["image_type"] == "review_card"]
    if len(rc) != 2:
        errs.append("expected 2 review_card posts, got {}".format(len(rc)))
    got = {p.get("prerendered_image") for p in rc}
    if got != REVIEW_CARDS:
        errs.append("review card paths mismatch: {}".format(sorted(got)))
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
    if len(mascot) != 3:
        errs.append("expected 3 mascot landmark posts, got {}".format(len(mascot)))
    for p in mascot:
        if p["image_type"] != "asset":
            errs.append("{}: mascot post must be image_type asset".format(p["id"]))

    return errs


def main():
    raw = POSTS_A + POSTS_B + POSTS_C
    posts = [expand(r, i + 1) for i, r in enumerate(raw)]

    errs = validate(posts)

    itypes = {}
    pillars = {}
    for p in posts:
        itypes[p["image_type"]] = itypes.get(p["image_type"], 0) + 1
        pillars[p["pillar"]] = pillars.get(p["pillar"], 0) + 1

    print("posts:      {}".format(len(posts)))
    print("pillars:    {}".format(dict(sorted(pillars.items()))))
    print("image_type: {}".format(dict(sorted(itypes.items()))))
    longest = max(posts, key=lambda p: len(p["twitter"]))
    print("longest tweet: {} chars ({})".format(len(longest["twitter"]), longest["id"]))
    print("review cards at: {}".format(
        [p["id"] for p in posts if p["image_type"] == "review_card"]))
    print("mascot posts at: {}".format(
        [(p["id"], p["topic"]) for p in posts if p["image_hint"] == "asset:logo_mascot"]))
    print("13:07 slots all personal: {}".format(
        all(p["pillar"] == "personal" for i, p in enumerate(posts) if i % 3 == 1)))

    if errs:
        print("\nVALIDATION FAILED ({} issues):".format(len(errs)))
        for e in errs:
            print("  x {}".format(e))
        sys.exit(1)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(posts, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print("\nVALIDATION PASSED — wrote {}".format(OUT))


if __name__ == "__main__":
    main()
