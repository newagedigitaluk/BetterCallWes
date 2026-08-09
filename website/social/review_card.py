"""
Review-card image generator for Better Call Wes social posts.

Renders a clean Google-style review card (white card on soft gradient,
5 gold stars, the review text, reviewer name) as a 1080x1080 PNG.

Why Pillow not AI: testimonials must be VERBATIM. AI image models garble
text. This renders the exact quote, deterministically. This format was the
single best-performing organic post (the "Another happy customer" card).

IMPORTANT: only ever feed this REAL reviews. Never fabricate testimonials.
Reviews live in reviews.json next to this file:
  [{ "name": "...", "stars": 5, "text": "...", "service": "power flush" }]

Usage:
  python3 review_card.py                 # render all reviews.json → cards/
  python3 review_card.py --one 0 out.png # render review index 0 to out.png
"""
import json
import os
import sys
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
REVIEWS_PATH = HERE / "reviews.json"
OUT_DIR = HERE / "review_cards"

# Brand
NAVY = (10, 37, 64)
ORANGE = (255, 107, 0)
GOLD = (251, 188, 5)       # Google star gold
INK = (32, 33, 36)
GREY = (95, 99, 104)
CARD = (255, 255, 255)

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

W = H = 1080


def _font(path, size):
    return ImageFont.truetype(path, size)


def _soft_background(draw):
    """Vertical soft navy→light gradient backdrop."""
    top = (225, 234, 243)
    bot = (243, 247, 250)
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)


def _rounded_rect(draw, box, radius, fill, shadow=False):
    x0, y0, x1, y1 = box
    if shadow:
        # simple offset shadow
        s = 8
        draw.rounded_rectangle([x0 + s, y0 + s, x1 + s, y1 + s], radius, fill=(0, 0, 0, 30))
    draw.rounded_rectangle(box, radius, fill=fill)


def _draw_star(draw, cx, cy, r, fill):
    """Draw a 5-point star centred at (cx, cy) with outer radius r."""
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


LOGO_PATH = Path(__file__).parent.parent / "site" / "assets" / "logo.png"

# Live profile stats shown in the footer — update when they grow
TOTAL_REVIEWS = 119
AVG_RATING = "5.0"


def _wrap(draw, text, font, avail_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= avail_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(review: dict, out_path: str):
    """On-brand review card: navy canvas, orange accents, BCW logo,
    white quote panel, gold stars, '5.0 from 119 reviews' social proof."""
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img, "RGBA")

    # Subtle radial glow behind the card so the navy isn't flat
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, -200, W + 200, H + 200], fill=22)
    img.paste(Image.new("RGB", (W, H), (16, 49, 82)), (0, 0), glow)
    draw = ImageDraw.Draw(img, "RGBA")

    # Brand orange accent bar across the very top (matches post banners)
    draw.rectangle([0, 0, W, 14], fill=ORANGE)

    # White quote panel
    card_box = [64, 84, W - 64, H - 84]
    cx0, cy0, cx1, cy1 = card_box
    draw.rounded_rectangle([cx0 + 7, cy0 + 9, cx1 + 7, cy1 + 9], 42, fill=(0, 0, 0, 70))
    draw.rounded_rectangle(card_box, 42, fill=CARD)

    # Logo centred at the top of the panel.
    # Threshold the alpha channel first — the source PNG has low-alpha noise
    # pixels around the artwork that render as dark speckles on white.
    y = cy0 + 52
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        alpha = logo.getchannel("A").point(lambda a: 255 if a > 200 else 0)
        logo.putalpha(alpha)
        logo = logo.crop(alpha.getbbox())  # tight crop to real artwork
        lw = 400
        lh = int(logo.height * lw / logo.width)
        logo = logo.resize((lw, lh), Image.LANCZOS)
        img.paste(logo, ((W - lw) // 2, y), logo)
        y += lh + 36
    else:
        y += 20

    # 5 gold stars, centred (gold = instant 'Google review' recognition)
    n = int(review.get("stars", 5))
    star_r, gap = 30, 84
    row_w = gap * 4
    sx = (W - row_w) // 2
    for i in range(5):
        _draw_star(draw, sx + i * gap, y + star_r, star_r,
                   GOLD if i < n else (225, 225, 225))
    y += star_r * 2 + 40

    # Quote text — auto-size to fit the space above the name/footer
    text = review.get("text", "").strip()
    pad = 84
    avail_w = (cx1 - pad) - (cx0 + pad)
    footer_top = cy1 - 150  # space reserved for name + footer
    chosen = None
    for size, lh in ((42, 58), (38, 52), (33, 46), (29, 41)):
        f_body = _font(FONT_REG, size)
        lines = _wrap(draw, text, f_body, avail_w)
        if y + len(lines) * lh <= footer_top:
            chosen = (f_body, lines, lh)
            break
    if chosen is None:
        chosen = (f_body, lines, lh)  # smallest size, may run tight
    f_body, lines, line_h = chosen

    # Big decorative orange quote mark, anchored to the quote block
    f_quote = _font(FONT_BOLD, 120)
    draw.text((cx0 + 36, y - 54), "“", font=f_quote, fill=ORANGE)

    # Vertically centre the quote block in the remaining space
    block_h = len(lines) * line_h
    y = y + max(0, (footer_top - y - block_h) // 2)
    for ln in lines:
        lw_px = draw.textlength(ln, font=f_body)
        draw.text(((W - lw_px) // 2, y), ln, font=f_body, fill=INK)
        y += line_h

    # Reviewer name — orange, centred
    f_name = _font(FONT_BOLD, 40)
    name = "— " + review.get("name", "Verified customer")
    nw = draw.textlength(name, font=f_name)
    draw.text(((W - nw) // 2, cy1 - 138), name, font=f_name, fill=ORANGE)

    # Footer: social proof line, centred, grey, with a small drawn gold star
    # (Liberation Sans has no ★ glyph — drawing it avoids a tofu box)
    f_foot = _font(FONT_REG, 28)
    left_part = "Verified Google review  ·  "
    right_part = f" {AVG_RATING} from {TOTAL_REVIEWS} reviews"
    star_d = 26
    total_w = (draw.textlength(left_part, font=f_foot) + star_d
               + draw.textlength(right_part, font=f_foot))
    fx = (W - total_w) // 2
    fy = cy1 - 76
    draw.text((fx, fy), left_part, font=f_foot, fill=GREY)
    fx += draw.textlength(left_part, font=f_foot)
    _draw_star(draw, fx + star_d // 2, fy + 16, star_d // 2, GOLD)
    fx += star_d
    draw.text((fx, fy), right_part, font=f_foot, fill=GREY)

    img.save(out_path)
    return out_path


def main():
    if not REVIEWS_PATH.exists():
        print(f"No reviews.json at {REVIEWS_PATH}. Create it with real reviews only.")
        sys.exit(1)
    reviews = json.loads(REVIEWS_PATH.read_text())

    if len(sys.argv) >= 3 and sys.argv[1] == "--one":
        idx = int(sys.argv[2])
        out = sys.argv[3] if len(sys.argv) > 3 else "review_card.png"
        render(reviews[idx], out)
        print(f"Rendered review {idx} → {out}")
        return

    OUT_DIR.mkdir(exist_ok=True)
    for i, r in enumerate(reviews):
        out = OUT_DIR / f"review-{i:02d}-{r.get('name','x').split()[0].lower()}.png"
        render(r, str(out))
        print(f"  ✅ {out.name}")
    print(f"\nRendered {len(reviews)} review cards to {OUT_DIR}")


if __name__ == "__main__":
    main()
