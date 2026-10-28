"""
Reel poster — publishes one Reel to Instagram + Facebook.

Runs 3x/week via cron, separate from the daily static post.

Footage priority:
  1. A real clip from website/social/reels/footage/  (best — real hands on
     real jobs is what performs for trades). Used oldest-first, then moved
     to footage/used/.
  2. Motion graphic built from the image library (Ken Burns + hook text).

Content comes from reels_bank.json — same pending/sent model as the static
content bank.

Usage:
  ZERNIO_API_KEY=... python3 post_reel.py            # publish next reel
  ZERNIO_API_KEY=... python3 post_reel.py --dry-run  # build only, no post
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

BANK_PATH = HERE / "reels_bank.json"

from reel_builder import build, next_footage, retire_footage  # noqa: E402
from image_picker import pick as pick_image  # noqa: E402
from post_daily import notify_telegram, log, in_window  # noqa: E402


def load_bank() -> dict:
    if not BANK_PATH.exists():
        log(f"❌ No reels bank at {BANK_PATH}")
        sys.exit(1)
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def save_bank(bank: dict):
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    dry = "--dry-run" in sys.argv
    bank = load_bank()
    pending = [r for r in bank["reels"] if r.get("status") == "pending"]
    # Dated reels (clocks going back, first frost) go first once their day
    # comes, and are skipped outside their window.
    pending = [r for r in pending if in_window(r)]
    pending.sort(key=lambda r: 0 if r.get("not_before") else 1)

    if not pending:
        log("❌ Reels bank is empty — no pending reels.")
        if not dry and datetime.now().hour < 14:
            notify_telegram("🎬 BCW reels: bank is EMPTY — no reels will post "
                            "until new ones are added.")
        sys.exit(1)

    reel = pending[0]
    remaining = len(pending) - 1
    log(f"🎬 Reel: '{reel['topic']}' ({remaining} left after this)")

    # ---- footage: real clip if Wes has dropped one in, else motion graphic
    clip = next_footage()
    base_image = None
    chosen = reel.get("base_image")
    if chosen and not os.path.isabs(chosen):
        chosen = str(HERE / chosen)
    if clip:
        log(f"🎥 Using real footage: {clip.name}")
    elif chosen and os.path.exists(chosen):
        # A photo picked for this reel when it was written, so the picture
        # matches what the hook is talking about.
        base_image = chosen
        log(f"🖼  Motion graphic from chosen photo {os.path.basename(chosen)}")
    else:
        base_image = pick_image("asset", used_log=[],
                                image_hint=reel.get("image_hint", "asset:boiler"))
        log(f"🖼  No footage available — motion graphic from {os.path.basename(base_image or '?')}")
        if not base_image:
            log("❌ No base image either — cannot build a reel.")
            sys.exit(1)

    out = f"/tmp/bcw_reel_{reel['id']}.mp4"
    try:
        build(caption=reel["hook"], body=reel.get("body", ""),
              base_image=base_image, footage=str(clip) if clip else None,
              out=out, seconds=reel.get("seconds", 11))
        log(f"✅ Built {os.path.basename(out)} ({os.path.getsize(out)//1024} KB)")
    except Exception as e:
        log(f"❌ Reel build failed: {e}")
        notify_telegram(f"🎬 BCW reels: build FAILED for {reel['id']} ({str(e)[:120]})")
        sys.exit(1)

    if dry:
        log(f"🔍 Dry run — built at {out}, nothing published.")
        return

    from zernio_client import ZernioClient
    z = ZernioClient()
    accounts = bank.get("accounts") or json.loads(
        (HERE / "content_bank.json").read_text(encoding="utf-8")
    )["meta"]["accounts"]

    try:
        video_url = z.upload_video(out)
    except Exception as e:
        log(f"❌ Video upload failed: {e}")
        notify_telegram(f"🎬 BCW reels: upload FAILED for {reel['id']} ({str(e)[:120]})")
        sys.exit(1)

    posted = []
    for platform in ("instagram", "facebook"):
        acct = accounts.get(platform)
        if not acct:
            continue
        text = reel.get(platform) or reel.get("caption", "")
        try:
            z.create_reel(text, platform, acct, video_url, video_path=out,
                          platform_data=(reel.get("platform_data") or {}).get(platform))
            posted.append(platform)
        except Exception as e:
            log(f"  ❌ {platform} reel failed: {e}")

    if not posted:
        notify_telegram(f"🎬 BCW reels: {reel['id']} failed on every platform.")
        sys.exit(1)

    reel["status"] = "sent"
    reel["sent_at"] = datetime.now(timezone.utc).isoformat()
    reel["video_url"] = video_url
    reel["used_footage"] = clip.name if clip else None
    save_bank(bank)
    if clip:
        retire_footage(clip)

    log(f"\n✅ Reel posted to {', '.join(posted)}: '{reel['topic']}'")
    log(f"   Reels remaining: {remaining}")
    if remaining <= 3 and datetime.now().hour < 14:
        notify_telegram(f"🎬 BCW reels: only {remaining} left in the bank.")


if __name__ == "__main__":
    main()
