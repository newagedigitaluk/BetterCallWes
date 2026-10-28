"""
Reel builder — makes 1080x1920 vertical MP4s for Instagram/Facebook Reels.

TWO SOURCES, in priority order:
  1. REAL FOOTAGE  — any clip Wes drops in website/social/reels/footage/.
     This is what actually performs for trades (the viral research was
     unambiguous: real hands doing real jobs beats anything produced).
     Clips are used oldest-first and moved to footage/used/ after posting.
  2. MOTION GRAPHIC — generated from a still from the image library:
     slow Ken Burns push + hook text + end card. Not as good as real
     footage, but it means 3 reels a week happen whether or not Wes filmed
     anything, and Reels get far more distribution than static posts.

Text is rendered with Pillow into a transparent PNG and composited by
ffmpeg, rather than using ffmpeg's drawtext — Pillow gives proper wrapping,
auto-sizing and the brand look already used on the static posts.

Usage:
  python3 reel_builder.py --caption "Why your rads are cold at the bottom" \
                          --body "Sludge sits in the bottom of the panel" \
                          --out /tmp/reel.mp4
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FOOTAGE_DIR = HERE / "reels" / "footage"
USED_DIR = FOOTAGE_DIR / "used"
LOGO = HERE.parent / "site" / "assets" / "logo.png"

W, H = 1080, 1920
FPS = 30
DEFAULT_SECONDS = 11

NAVY = (10, 37, 64)
ORANGE = (255, 107, 0)
WHITE = (255, 255, 255)

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _strip_emoji(s: str) -> str:
    """Liberation Sans has no emoji glyphs — they render as tofu boxes."""
    return " ".join("".join(c for c in (s or "") if ord(c) < 0x2000).split())


def build_overlay(caption: str, body: str = "", out_png: str = None) -> str:
    """Transparent 1080x1920 PNG: hook banner at top, optional body line,
    brand strip + CTA at the bottom."""
    out_png = out_png or tempfile.mktemp(suffix=".png")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ---- hook block, top third (must be readable in the first frame) ----
    caption = _strip_emoji(caption)
    size = 86
    while size > 46:
        f = ImageFont.truetype(FONT_BOLD, size)
        lines = _wrap(d, caption, f, W - 140)
        if len(lines) <= 3:
            break
        size -= 6
    line_h = int(size * 1.18)
    block_h = line_h * len(lines)
    top = 250
    # dark scrim so text stays readable over any photo
    d.rectangle([0, top - 60, W, top + block_h + 46], fill=NAVY + (219,))
    d.rectangle([0, top - 60, W, top - 52], fill=ORANGE + (255,))
    y = top
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y), ln, font=f, fill=WHITE)
        y += line_h

    # ---- body line, under the hook ----
    body = _strip_emoji(body)
    if body:
        # Own navy panel: a drop shadow alone vanished over white boilers
        # and radiators, which is most of what we film.
        fb = ImageFont.truetype(FONT_REG, 46)
        blines = _wrap(d, body, fb, W - 200)[:3]
        by = top + block_h + 90
        d.rectangle([60, by - 22, W - 60, by + 60 * len(blines) + 10],
                    fill=NAVY + (200,))
        for ln in blines:
            tw = d.textlength(ln, font=fb)
            d.text(((W - tw) / 2, by), ln, font=fb, fill=WHITE)
            by += 60

    # ---- bottom brand strip ----
    # Strip must be tall enough for logo AND the CTA line beneath it; at
    # 210px with a 420px-wide logo the two overlapped.
    strip_h = 300
    d.rectangle([0, H - strip_h, W, H], fill=NAVY + (232,))
    d.rectangle([0, H - strip_h, W, H - strip_h + 8], fill=ORANGE + (255,))

    cta_y = H - 78
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        a = logo.getchannel("A").point(lambda v: 255 if v > 200 else 0)
        logo.putalpha(a)
        bbox = a.getbbox()
        if bbox:
            logo = logo.crop(bbox)
        lw = 340
        lh = int(logo.height * lw / logo.width)
        logo = logo.resize((lw, lh), Image.LANCZOS)
        logo_y = H - strip_h + 30
        img.paste(logo, ((W - lw) // 2, logo_y), logo)
        cta_y = max(cta_y, logo_y + lh + 22)  # always clear of the logo

    fcta = ImageFont.truetype(FONT_BOLD, 38)
    cta = "Southampton  ·  07700 155 655"
    tw = d.textlength(cta, font=fcta)
    d.text(((W - tw) / 2, cta_y), cta, font=fcta, fill=WHITE)

    img.save(out_png)
    return out_png


def _run(cmd: list, timeout: int = 300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr.strip()[-400:]}")
    return r


def next_footage() -> Path | None:
    """Oldest unused clip Wes has dropped in, if any."""
    if not FOOTAGE_DIR.exists():
        return None
    clips = [p for p in FOOTAGE_DIR.iterdir()
             if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    return min(clips, key=lambda p: p.stat().st_mtime) if clips else None


def build(caption: str, body: str = "", base_image: str = None,
          footage: str = None, out: str = "/tmp/reel.mp4",
          seconds: int = DEFAULT_SECONDS) -> str:
    """Build a vertical reel. Uses `footage` if given, else Ken Burns on
    `base_image`."""
    overlay = build_overlay(caption, body)

    if footage:
        # Real clip: fit to 1080x1920, trim, composite overlay, strip audio
        # issues by re-encoding cleanly.
        _run([
            "ffmpeg", "-y", "-i", str(footage), "-i", overlay,
            "-filter_complex",
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},fps={FPS}[v];[v][1:v]overlay=0:0[o]",
            "-map", "[o]", "-map", "0:a?", "-t", str(seconds),
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", out,
        ], timeout=600)
    else:
        # Motion graphic: slow push in on the still (Ken Burns).
        zoom_frames = seconds * FPS
        _run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(base_image), "-i", overlay,
            "-filter_complex",
            # upscale first so zoompan doesn't soften the image
            f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
            f"crop={W*2}:{H*2},"
            f"zoompan=z='min(zoom+0.0006,1.18)':d={zoom_frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}[v];"
            f"[v][1:v]overlay=0:0[o]",
            "-map", "[o]", "-t", str(seconds),
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out,
        ], timeout=600)

    try:
        os.unlink(overlay)
    except OSError:
        pass
    return out


def retire_footage(clip: Path):
    """Move a used clip aside so it isn't posted twice."""
    USED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(clip), str(USED_DIR / clip.name))
    except Exception as e:
        print(f"  [reel] could not move used clip: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--caption", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--image", default=None)
    ap.add_argument("--footage", default=None)
    ap.add_argument("--out", default="/tmp/reel.mp4")
    a = ap.parse_args()
    print(build(a.caption, a.body, a.image, a.footage, a.out))
