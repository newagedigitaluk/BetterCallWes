"""
Zernio / platform limits, transcribed from the official docs (docs.zernio.com),
plus a preflight validator so we never ship a post that the platform will reject.

Sources (read 2026-08-24):
  docs.zernio.com                       — auth, POST /posts shape, platform list
  docs.zernio.com/guides/media-uploads  — media flow, per-platform media counts
  docs.zernio.com/guides/rate-limits    — 429 + Retry-After semantics
  docs.zernio.com/guides/idempotency    — x-request-id, duplicate protection
  docs.zernio.com/platforms/instagram   — IG caption/image/video specs
  docs.zernio.com/platforms/facebook    — FB caption/image/video specs
  docs.zernio.com/platforms/google-business — GBP specs

Anything marked NOT DOCUMENTED is genuinely absent from the docs — don't
invent a value for it later, go and check the guide again.
"""
from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Text limits
# ---------------------------------------------------------------------------
TEXT_LIMITS = {
    "instagram":      2200,    # caption
    "facebook":       63206,   # truncated at ~480 with "See more"
    "googlebusiness": 1500,
    "twitter":        280,     # NOT DOCUMENTED by Zernio; platform limit
}

# Visible before the "more" fold — front-load the hook inside this many chars.
FOLD = {"instagram": 125, "facebook": 480}

# ---------------------------------------------------------------------------
# Image limits
# ---------------------------------------------------------------------------
IMAGE_MAX_BYTES = {
    "instagram":      8 * 1024 * 1024,   # auto-compressed above this
    "facebook":       4 * 1024 * 1024,   # FB rejects larger in practice
    "googlebusiness": 5 * 1024 * 1024,
}
IMAGE_FORMATS = {
    "instagram":      {"jpg", "jpeg", "png"},
    "facebook":       {"jpg", "jpeg", "png", "gif"},   # WebP auto-converted
    "googlebusiness": {"jpg", "jpeg", "png"},          # WebP auto-converted
}
GBP_MIN_DIMENSIONS = (400, 300)

# Instagram feed accepts 0.8 (4:5) .. 1.91 (1.91:1).
# 4:5 / 1080x1350 is documented as "Best engagement for feed posts".
IG_FEED_BEST = (1080, 1350)
IG_FEED_RATIO_RANGE = (0.8, 1.91)

# ---------------------------------------------------------------------------
# Video / Reels limits
# ---------------------------------------------------------------------------
REEL_SPEC = {
    "instagram": {"min_s": 3, "max_s": 90,  "max_bytes": 300 * 1024 * 1024},
    "facebook":  {"min_s": 3, "max_s": 60,  "max_bytes": 4 * 1024**3},
}
REEL_RESOLUTION = (1080, 1920)   # 9:16
REEL_CODEC = "h264"
REEL_FPS = 30

# Google Business does NOT support video via the API.
VIDEO_UNSUPPORTED = {"googlebusiness"}

# ---------------------------------------------------------------------------
# Quotas
# ---------------------------------------------------------------------------
IG_POSTS_PER_24H = 100          # all content types combined
GBP_POST_VISIBLE_DAYS = 7       # archived after ~7 days; post weekly minimum


# Google Business post buttons (platforms[].platformSpecificData.callToAction).
GBP_CTA_TYPES = {"LEARN_MORE", "BOOK", "ORDER", "SHOP", "SIGN_UP", "CALL"}


class PostValidationError(ValueError):
    """Raised when a post would breach a documented platform limit."""


def _ext(path_or_url: str) -> str:
    return os.path.splitext((path_or_url or "").split("?")[0])[1].lstrip(".").lower()


def validate_text(platform: str, text: str) -> list[str]:
    """Hard errors for text. Returns [] if fine."""
    errs = []
    limit = TEXT_LIMITS.get(platform)
    if limit and len(text or "") > limit:
        errs.append(f"{platform}: text is {len(text)} chars, limit is {limit}")
    if not (text or "").strip():
        errs.append(f"{platform}: empty content")
    return errs


def validate_image(platform: str, local_path: str | None) -> list[str]:
    """Hard errors for an image attachment. local_path may be None (already
    uploaded) in which case only what we can check is checked."""
    errs = []
    if not local_path or not os.path.exists(local_path):
        return errs
    size = os.path.getsize(local_path)
    cap = IMAGE_MAX_BYTES.get(platform)
    if cap and size > cap:
        errs.append(f"{platform}: image is {size//1024//1024}MB, limit is {cap//1024//1024}MB")
    fmts = IMAGE_FORMATS.get(platform)
    ext = _ext(local_path)
    if fmts and ext and ext not in fmts and ext != "webp":  # webp is auto-converted
        errs.append(f"{platform}: image format .{ext} not accepted (need {sorted(fmts)})")
    if platform == "googlebusiness":
        try:
            from PIL import Image
            w, h = Image.open(local_path).size
            if w < GBP_MIN_DIMENSIONS[0] or h < GBP_MIN_DIMENSIONS[1]:
                errs.append(f"googlebusiness: {w}x{h} is below the {GBP_MIN_DIMENSIONS} minimum")
        except Exception:
            pass
    return errs


def validate_video(platform: str, local_path: str | None,
                   duration_s: float | None = None) -> list[str]:
    """Hard errors for a video/Reel attachment."""
    errs = []
    if platform in VIDEO_UNSUPPORTED:
        errs.append(f"{platform}: video is not supported via the API")
        return errs
    spec = REEL_SPEC.get(platform)
    if not spec:
        return errs
    if local_path and os.path.exists(local_path):
        size = os.path.getsize(local_path)
        if size > spec["max_bytes"]:
            errs.append(f"{platform}: video is {size//1024//1024}MB, "
                        f"limit is {spec['max_bytes']//1024//1024}MB")
        if duration_s is None:
            duration_s = probe_duration(local_path)
    if duration_s is not None:
        if duration_s < spec["min_s"]:
            errs.append(f"{platform}: video is {duration_s:.1f}s, minimum is {spec['min_s']}s")
        if duration_s > spec["max_s"]:
            errs.append(f"{platform}: video is {duration_s:.1f}s, maximum is {spec['max_s']}s")
    return errs


def probe_duration(path: str) -> float | None:
    """Video duration in seconds via ffprobe, or None."""
    import subprocess
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except Exception:
        return None


def validate(platform: str, text: str, image_path: str | None = None,
             video_path: str | None = None, raise_on_error: bool = False) -> list[str]:
    """Full preflight for one platform. Returns a list of problems."""
    errs = validate_text(platform, text)
    if image_path:
        errs += validate_image(platform, image_path)
    if video_path:
        errs += validate_video(platform, video_path)
    if errs and raise_on_error:
        raise PostValidationError("; ".join(errs))
    return errs


def validate_platform_data(platform: str, data: dict) -> list[str]:
    """Check the platformSpecificData extras we send."""
    errs = []
    if platform == "googlebusiness" and "callToAction" in data:
        cta = data["callToAction"] or {}
        if cta.get("type") not in GBP_CTA_TYPES:
            errs.append(f"googlebusiness: callToAction type {cta.get('type')!r} not in {sorted(GBP_CTA_TYPES)}")
        if cta.get("type") != "CALL" and not str(cta.get("url", "")).startswith("https://"):
            errs.append("googlebusiness: callToAction url must be https")
    if "firstComment" in data:
        if platform != "instagram" and platform != "facebook":
            errs.append(f"{platform}: firstComment is not supported")
        errs += [e.replace("text", "first comment") for e in
                 validate_text(platform, data["firstComment"])]
    return errs
