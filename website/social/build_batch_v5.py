#!/usr/bin/env python3
"""Build batch v5: 30 static posts + 12 reels, every image made up front.

Stages the batch for review rather than loading it:
  new_posts_batch_v5.json   posts, same shape as content_bank.json entries
  reels_batch_v5.json       reels, same shape as reels_bank.json entries
  images/v5/                finished 1080x1350 post images + reel bases

Nothing posts until `--merge`, which appends both to the live banks. Run
create_post_links.py after merging to create the WhatsApp short links.

Run:  python3 build_batch_v5.py            # build + validate
      python3 build_batch_v5.py --merge    # after Wes approves
"""
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import caption_banner  # noqa: E402
import zernio_limits as limits  # noqa: E402
from _v5_posts import NUM, POSTS, REELS  # noqa: E402

BRAND = HERE.parent / "Brand Images"
WORK = BRAND / "Work Images"
OUT = HERE / "images" / "v5"
SRC = OUT / "src"          # GPT Image 2.5 renders, kept so the build reruns
SHORT = "https://u.bettercallwes.co.uk/"
WA_NUMBER = "447700155655"
IG_BIO_LINE = "Or tap WhatsApp in our bio."

# GPT Image 2.5 renders (Higgsfield), scratch name -> file. Copied into SRC
# on first build so the batch doesn't depend on the scratch directory.
GEN_SCRATCH = Path("/tmp/claude-1000/-home-wes-Coding-Projects-Better-Call-Wes/"
                   "cf1a2dcb-b49a-4c5a-ab23-cbf2ae34ee81/scratchpad/gen")
GEN_FILES = {
    "thermostat": "thermostat.png", "vaillant_reset": "vaillant_reset.png",
    "service_torch": "service_torch.png", "ideal_logic": "ideal_logic.png",
    "bleed_rad": "bleed_rad.png", "clipboard_vaillant": "clipboard_vaillant.png",
    "worcester_panel": "worcester_panel.png", "condensate_frost": "condensate_frost.png",
    "gauge_crouch": "gauge_crouch.png", "stopcock": "stopcock.png",
    "wes_boiler": "wes_boiler_flare.png", "meter_sunburst": "meter_v2_sunburst.png",
    "meter_flare": "meter_v2_flare.png",
}

NAVY = (10, 37, 64)
WHITE = (255, 255, 255)
ORANGE = (255, 107, 0)
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def gen_source(name: str) -> Path:
    dst = SRC / f"{name}.jpg"
    if not dst.exists():
        SRC.mkdir(parents=True, exist_ok=True)
        Image.open(GEN_SCRATCH / GEN_FILES[name]).convert("RGB").save(dst, "JPEG", quality=92)
    return dst


def hx_crops() -> tuple:
    """New and old heat exchangers from IMG_1902, cropped clear of the old
    NEW AGE branding printed on the mat underneath."""
    im = ImageOps.exif_transpose(Image.open(WORK / "IMG_1902.jpg")).convert("RGB")
    w, h = im.size
    new = im.crop((int(.03 * w), int(.24 * h), int(.47 * w), int(.64 * h)))
    old = im.crop((int(.495 * w), int(.18 * h), int(.93 * w), int(.64 * h)))
    return new, old


def hx_card(banner: str, out: Path) -> Path:
    """New exchanger above the one that came out, labelled, on navy."""
    W, H = 1080, 1350
    card = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(card)
    top = int(W * caption_banner.BANNER_FRAC) + 20
    slot = (H - top - 20) // 2
    font = ImageFont.truetype(FONT, 40)
    for i, (img, label) in enumerate(zip(hx_crops(), ("New", "What came out"))):
        img = img.copy()
        img.thumbnail((W - 40, slot - 20), Image.LANCZOS)
        x, y = (W - img.width) // 2, top + i * slot
        card.paste(img, (x, y))
        # Label as an orange tag on the photo itself, so it can't be read
        # as belonging to the picture above or below.
        tw = int(d.textlength(label, font=font))
        d.rectangle([x, y, x + tw + 32, y + 58], fill=ORANGE)
        d.text((x + 16, y + 8), label, font=font, fill=WHITE)
    tmp = OUT / "_hx_base.jpg"
    card.save(tmp, "JPEG", quality=92)
    caption_banner.render(str(tmp), banner, str(out), position="top", height=H, anchor_y=0)
    tmp.unlink()
    return out


def source_path(src: str) -> Path:
    kind, name = src.split(":", 1)
    if kind == "gen":
        return gen_source(name)
    if kind == "work":
        return WORK / name
    if kind == "brand":
        return BRAND / name
    if kind == "card" and name == "hx_old":
        p = OUT / "reels" / "hx_old.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        hx_crops()[1].save(p, "JPEG", quality=92)
        return p
    raise ValueError(f"unknown image source {src}")


def wa_link(text: str) -> str:
    return f"https://wa.me/{WA_NUMBER}?text={quote(text)}"


def build_posts(start_id: int) -> list:
    posts = []
    for n, p in enumerate(POSTS, 1):
        img = p["img"]
        out = OUT / f"{n:02d}-{p['key']}.jpg"
        if img["src"] == "card:hx":
            hx_card(img["banner"], out)
        else:
            caption_banner.render(str(source_path(img["src"])), img["banner"], str(out),
                                  position=img.get("pos", "top"), height=1350,
                                  anchor_y=img.get("anchor", 0.5))
        cta = p["cta"].format(num=NUM)
        slug = f"wa-{p['key']}"
        link = SHORT + slug
        post = {
            "id": f"post_{start_id + n - 1}",
            "batch": "v5",
            "format": p["fmt"],
            "pillar": p["pillar"],
            "topic": img["banner"],
            "service_slug": p["slug"],
            # create_post_links.py shortens service_url, so this is where
            # the per-post WhatsApp link (with its opening message) lives.
            "service_url": wa_link(p["wa"]),
            "short_link_slug": slug,
            "instagram": f"{p['body']}\n\n{cta}\n{IG_BIO_LINE}\n\n{p['tags']}",
            "facebook": f"{p['body']}\n\n{cta}\nTap to open WhatsApp: {link}",
            "googlebusiness": f"{p['body']}\n\n{cta}",
            # Links only work where the platform makes them work: Instagram
            # captions never do, so the link goes in the first comment (and
            # the bio); Google Business gets a real Book button.
            "platform_data": {
                "instagram": {"firstComment": f"WhatsApp Wes: {link}"},
                "googlebusiness": {"callToAction": {"type": "BOOK", "url": link}},
            },
            "twitter": "",
            "image_type": "prerendered",
            "image_hint": "prerendered",
            "caption": img["banner"],
            "image_prompt": "",
            "prerendered_image": str(out.relative_to(HERE)),
            "image_source": img["src"],
            "status": "pending",
        }
        for k in ("not_before", "not_after", "check"):
            if p.get(k):
                post[k] = p[k]
        posts.append(post)
    return posts


def build_reels(start_n: int) -> list:
    reels = []
    rdir = OUT / "reels"
    rdir.mkdir(parents=True, exist_ok=True)
    for n, r in enumerate(REELS, start_n):
        src = source_path(r["src"])
        base = rdir / f"reel_{n:03d}-{r['key']}.jpg"
        if src != base:
            ImageOps.exif_transpose(Image.open(src)).convert("RGB").save(base, "JPEG", quality=92)
        slug = f"wa-reel-{r['key']}"
        cta = f"WhatsApp {NUM} to book."
        reel = {
            "id": f"reel_{n:03d}",
            "batch": "v5",
            "status": "pending",
            "topic": r["hook"],
            "hook": r["hook"],
            "body": r["body"],
            "base_image": str(base.relative_to(HERE)),
            "image_hint": "prerendered",
            "seconds": r["seconds"],
            "service_url": wa_link("Hi Wes, I saw your reel and I'd like to book."),
            "short_link_slug": slug,
            "instagram": f"{r['caption']}\n\n{cta}\n{IG_BIO_LINE}\n\n#Southampton #BoilerRepair #GasSafe #Reels",
            "facebook": f"{r['caption']}\n\n{cta}\nTap to open WhatsApp: {SHORT}{slug}",
            "platform_data": {"instagram": {"firstComment": f"WhatsApp Wes: {SHORT}{slug}"}},
        }
        for k in ("not_before", "not_after"):
            if r.get(k):
                reel[k] = r[k]
        reels.append(reel)
    return reels


BANNED = ["—", " – ", "VAT", "558654", "Comment QUOTE", "DM you"]


def validate(posts: list, reels: list) -> list:
    problems = []
    for p in posts:
        for plat in ("instagram", "facebook", "googlebusiness"):
            problems += [f"{p['id']}: {e}" for e in limits.validate_text(plat, p[plat])]
            problems += [f"{p['id']}: {e}" for e in
                         limits.validate_image(plat, str(HERE / p["prerendered_image"]))]
            for b in BANNED:
                if b in p[plat]:
                    problems.append(f"{p['id']} {plat}: contains banned text {b!r}")
        for plat, extra in p.get("platform_data", {}).items():
            problems += [f"{p['id']}: {e}" for e in limits.validate_platform_data(plat, extra)]
        # The hook (first sentence) must land before Instagram's "more" fold.
        m = re.search(r"[.?!]", p["instagram"])
        if not m or m.end() > limits.FOLD["instagram"]:
            problems.append(f"{p['id']}: opening sentence runs past Instagram's 125-char fold")
    for r in reels:
        for plat in ("instagram", "facebook"):
            problems += [f"{r['id']}: {e}" for e in limits.validate_text(plat, r[plat])]
            for b in BANNED:
                if b in r[plat] or b in r["hook"] or b in r["body"]:
                    problems.append(f"{r['id']}: contains banned text {b!r}")
    return problems


def main():
    bank = json.loads((HERE / "content_bank.json").read_text(encoding="utf-8"))
    rbank = json.loads((HERE / "reels_bank.json").read_text(encoding="utf-8"))
    next_post = max(int(p["id"].split("_")[1]) for p in bank["posts"]) + 1
    next_reel = max(int(r["id"].split("_")[1]) for r in rbank["reels"]) + 1

    if "--merge" in sys.argv:
        posts = json.loads((HERE / "new_posts_batch_v5.json").read_text(encoding="utf-8"))
        reels = json.loads((HERE / "reels_batch_v5.json").read_text(encoding="utf-8"))
        have = {p["id"] for p in bank["posts"]}
        bank["posts"] += [p for p in posts if p["id"] not in have]
        have = {r["id"] for r in rbank["reels"]}
        rbank["reels"] += [r for r in reels if r["id"] not in have]
        (HERE / "content_bank.json").write_text(json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
        (HERE / "reels_bank.json").write_text(json.dumps(rbank, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Merged {len(posts)} posts and {len(reels)} reels. Now run create_post_links.py.")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    posts = build_posts(next_post)
    reels = build_reels(next_reel)
    problems = validate(posts, reels)
    (HERE / "new_posts_batch_v5.json").write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    (HERE / "reels_batch_v5.json").write_text(json.dumps(reels, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(posts)} posts ({posts[0]['id']}..{posts[-1]['id']}) "
          f"and {len(reels)} reels ({reels[0]['id']}..{reels[-1]['id']})")
    if problems:
        print("\nPROBLEMS:")
        for x in problems:
            print("  -", x)
        sys.exit(1)
    print("Validation: clean")


if __name__ == "__main__":
    main()
