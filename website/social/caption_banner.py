"""
Local caption-banner renderer (Pillow) — the resilient fallback for post images.

WHY THIS EXISTS
---------------
Most BCW posts are "real photo + navy caption banner". We generate that with
GPT Image 2 via Higgsfield, which looks great — but it's an image-to-image
call, and it needs Higgsfield to accept an upload of the base photo. When
their upload endpoint degrades (SignatureDoesNotMatch, 2026-08-17→20) EVERY
image-to-image post fails, and the pipeline falls back to posting a bare,
unbranded photo with no caption at all.

A navy rectangle with white text does not need a neural network. This renders
exactly that, locally, deterministically, in milliseconds — so an outage
degrades to "correct branded image" instead of "bare photo".

Order of preference in post_daily.py:
  1. Higgsfield GPT Image 2  (best — matches the established look)
  2. this renderer           (near-identical, never fails, free)
  3. bare base photo         (last resort)

Text is rendered verbatim — no hallucination, no spelling drift, which is
also why review cards use Pillow rather than AI.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

# Brand
NAVY = (10, 37, 64)
ORANGE = (255, 107, 0)
WHITE = (255, 255, 255)

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

SIZE = 1080           # square, matches the AI output
BANNER_FRAC = 0.14    # banner height as a fraction of image height
BANNER_ALPHA = 224    # ~88% opacity, matching the prompt spec
ACCENT_PX = 4


def _fit(img: Image.Image, width: int = SIZE, height: int = SIZE,
         anchor_y: float = 0.5) -> Image.Image:
    """Crop to width:height and resize, so any source aspect works.

    anchor_y picks which part of a too-tall photo survives the crop:
    0 keeps the top, 0.5 the middle, 1 the bottom.
    """
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    target = width / height
    if w / h > target:                      # too wide: trim the sides
        cw = int(h * target)
        img = img.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    else:                                   # too tall: trim top/bottom
        ch = int(w / target)
        top = int((h - ch) * anchor_y)
        img = img.crop((0, top, w, top + ch))
    return img.resize((width, height), Image.LANCZOS)


def _best_font_size(draw, text, max_w, start=64, floor=30):
    """Largest font size that fits the caption on one line."""
    for pt in range(start, floor - 1, -2):
        f = ImageFont.truetype(FONT_BOLD, pt)
        if draw.textlength(text, font=f) <= max_w:
            return f
    return ImageFont.truetype(FONT_BOLD, floor)


def render(base_image_path: str, caption: str, out_path: str,
           position: str = "top", height: int = SIZE,
           anchor_y: float = 0.5) -> str:
    """Render base photo + brand caption banner to out_path. Returns out_path.

    position: "top" (default) or "bottom" — mirrors the AI prompt's
    upper-third / lower-third choice.
    height:   1080 for square, 1350 for Instagram's 4:5 feed shape.
    """
    img = _fit(Image.open(base_image_path), SIZE, height, anchor_y)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    banner_h = int(SIZE * BANNER_FRAC)
    y0 = 0 if position == "top" else height - banner_h
    y1 = y0 + banner_h

    # Navy banner
    draw.rectangle([0, y0, SIZE, y1], fill=NAVY + (BANNER_ALPHA,))
    # Orange accent along the banner's outer edge
    accent_y = y0 if position == "top" else y1 - ACCENT_PX
    draw.rectangle([0, accent_y, SIZE, accent_y + ACCENT_PX], fill=ORANGE + (255,))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Caption — emoji aren't in Liberation Sans and render as tofu, so strip
    # anything outside the basic printable range and tidy the spacing.
    text = "".join(ch for ch in (caption or "") if ord(ch) < 0x2000).strip()
    text = " ".join(text.split())
    if text:
        font = _best_font_size(draw, text, max_w=int(SIZE * 0.88))
        tw = draw.textlength(text, font=font)
        bbox = font.getbbox(text)
        th = bbox[3] - bbox[1]
        tx = (SIZE - tw) / 2
        ty = y0 + (banner_h - th) / 2 - bbox[1]
        draw.text((tx, ty), text, font=font, fill=WHITE)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=92)  # JPEG = Instagram-safe
    return out_path


if __name__ == "__main__":
    out = render("website/site/assets/images/heating-radiator.webp",
                 "Cold at the top? Trapped air", "/tmp/banner_demo.jpg")
    print("rendered:", out)
