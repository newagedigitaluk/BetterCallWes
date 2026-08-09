"""
Daily social media poster for Better Call Wes.

Picks the next pending post from content_bank.json, generates/selects
an image via Kie AI (with optional real photo base), and posts to
Facebook, Instagram, and Twitter via Zernio.

Usage:
  python social/post_daily.py           # Live posting
  python social/post_daily.py --dry-run # Preview only, no API calls

Cron example (8am daily):
  0 8 * * * cd "/home/wes/Coding/Projects/Better Call Wes" && \
    ZERNIO_API_KEY=sk_... KIE_API_KEY=... \
    python social/post_daily.py >> social/post.log 2>&1
"""

import sys
import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_BANK_PATH = PROJECT_ROOT / "social" / "content_bank.json"
LOG_PATH = PROJECT_ROOT / "social" / "post.log"

# Add social/ to path for sibling imports
sys.path.insert(0, str(PROJECT_ROOT / "social"))


def load_content_bank() -> dict:
    if not CONTENT_BANK_PATH.exists():
        print("❌ content_bank.json not found. Run setup_accounts.py first.")
        sys.exit(1)
    with open(CONTENT_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_content_bank(bank: dict):
    with open(CONTENT_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)


def log(message: str):
    """Print and optionally log to file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)


def notify_telegram(text: str) -> bool:
    """Send an ops alert to Wes's Telegram (BCW channel). Best-effort —
    never raises; posting must not fail because an alert couldn't send.

    Added after Kie credits silently ran out on 2026-05-30 and Instagram
    went dark for 12 days with nobody noticing."""
    try:
        import requests
        env_path = Path.home() / ".claude" / "channels" / "telegram-bcw" / ".env"
        access_path = Path.home() / ".claude" / "channels" / "telegram-bcw" / "access.json"
        token = None
        for ln in env_path.read_text().splitlines():
            if ln.startswith("TELEGRAM_BOT_TOKEN="):
                token = ln.split("=", 1)[1].strip()
        chat_id = json.loads(access_path.read_text())["allowFrom"][0]
        if not token or not chat_id:
            return False
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log(f"  (telegram alert failed: {e})")
        return False


def get_next_post(bank: dict) -> dict | None:
    """Return first approved post, or first pending post if none approved."""
    for post in bank["posts"]:
        if post.get("status") == "approved":
            return post
    for post in bank["posts"]:
        if post.get("status") == "pending":
            return post
    return None


def count_pending(bank: dict) -> int:
    return sum(1 for p in bank["posts"] if p.get("status") in ("pending", "approved"))


def get_accounts(bank: dict) -> dict:
    """Return account IDs from bank meta. Warn if core platforms are missing."""
    accounts = bank.get("meta", {}).get("accounts", {})
    # facebook and instagram are required; twitter is optional
    missing = [p for p in ["facebook", "instagram"] if not accounts.get(p)]
    if missing:
        print(f"⚠️  Missing account IDs for: {', '.join(missing)}")
        print("   Run: python social/setup_accounts.py")
    if not accounts.get("twitter"):
        log("  ℹ️  No Twitter/X account — connect one at zernio.com to enable X posts")
    return accounts


def get_used_log(bank: dict, image_type: str) -> list:
    meta = bank.get("meta", {})
    if image_type == "brand":
        return meta.get("used_brand_images", [])
    elif image_type == "work":
        return meta.get("used_work_images", [])
    elif image_type == "asset":
        return meta.get("used_asset_images", [])
    return []


def update_used_log(bank: dict, image_type: str, image_path: str):
    """Add image to used log, keeping only last 30 entries."""
    meta = bank.setdefault("meta", {})
    key_map = {
        "brand": "used_brand_images",
        "work": "used_work_images",
        "asset": "used_asset_images",
    }
    key = key_map.get(image_type)
    if key and image_path:
        log_list = meta.setdefault(key, [])
        if image_path not in log_list:
            log_list.append(image_path)
        # Keep last 30
        meta[key] = log_list[-30:]


def dry_run_display(post: dict, image_path: str | None):
    """Print what would be posted without making any API calls."""
    print("\n" + "=" * 60)
    print(f"  DRY RUN — Post: {post['id']} | Pillar: {post['pillar']}")
    print("=" * 60)
    print(f"\n📌 Topic:       {post['topic']}")
    print(f"🔗 Service URL: {post.get('service_url', 'N/A')}")
    print(f"🖼  Image type:  {post['image_type']}")
    print(f"💬 Caption:     {post.get('caption', 'N/A')}")

    if image_path:
        print(f"📸 Real photo:  {os.path.basename(image_path)}")
    else:
        print(f"🎨 AI generate: {post.get('image_prompt', 'N/A')[:80]}...")

    gb_text = post.get("googlebusiness") or post.get("facebook", "")
    print(f"\n--- FACEBOOK ---\n{post['facebook']}")
    print(f"\n--- INSTAGRAM ---\n{post['instagram']}")
    print(f"\n--- TWITTER ---\n{post['twitter']}")
    print(f"\n  Twitter length: {len(post['twitter'])} chars")
    print(f"\n--- GOOGLE BUSINESS ---\n{gb_text}")
    print("=" * 60)


def post_to_platforms(
    post: dict,
    accounts: dict,
    media_url: str,
    dry_run: bool = False,
):
    """Post to Facebook, Instagram, Twitter via Zernio."""
    if dry_run:
        return

    from zernio_client import ZernioClient
    client = ZernioClient()

    # Build platform list — use dedicated content per platform
    # Google Business falls back to Facebook text if no dedicated field
    gb_text = post.get("googlebusiness") or post.get("facebook", "")

    platforms = [
        ("facebook",      post.get("facebook", "")),
        ("instagram",     post.get("instagram", "")),
        ("twitter",       post.get("twitter", "")),
        ("googlebusiness", gb_text),
    ]

    results = {}
    for platform, content in platforms:
        account_id = accounts.get(platform)
        if not account_id:
            log(f"  ℹ️  Skipping {platform} — no account ID configured")
            continue
        if not content.strip():
            log(f"  ℹ️  Skipping {platform} — no content")
            continue
        # Retry transient failures (5xx / timeouts). Zernio intermittently
        # returns 503, which used to silently drop a whole platform for that
        # post. 4xx are NOT retried — those are our payload's fault and
        # retrying just repeats the same rejection.
        last_err = None
        for attempt in range(1, 4):
            try:
                result = client.create_post(
                    content=content,
                    platform=platform,
                    account_id=account_id,
                    media_url=media_url,
                )
                results[platform] = result.get("id", "posted")
                log(f"  ✅ {platform.capitalize()}: posted successfully"
                    + (f" (attempt {attempt})" if attempt > 1 else ""))
                last_err = None
                break
            except Exception as e:
                last_err = e
                status = getattr(getattr(e, "response", None), "status_code", None)
                transient = status is None or status >= 500 or status == 429
                if transient and attempt < 3:
                    wait = attempt * 5
                    log(f"  ⏳ {platform.capitalize()} attempt {attempt} failed "
                        f"({status or type(e).__name__}) — retrying in {wait}s")
                    time.sleep(wait)
                    continue
                break
        if last_err is not None:
            log(f"  ❌ {platform.capitalize()} failed: {last_err}")
            results[platform] = f"ERROR: {last_err}"
            notify_telegram(
                f"⚠️ BCW social: {platform} post FAILED for {post.get('id','?')} "
                f"({str(last_err)[:120]}). Other platforms may have gone out."
            )

    return results


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        log("🔍 DRY RUN MODE — no posts will be published")

    # Load content bank
    bank = load_content_bank()

    # Check pending posts
    pending = count_pending(bank)
    if pending == 0:
        log("❌ Content bank is empty! No pending posts.")
        log("   Generate more: python social/generate_posts.py <posts.json>")
        # ALERT: empty bank = posting has STOPPED. This early-exit used to
        # happen silently — the bank ran dry on 2026-06-12 and nothing posted
        # for 2 days before anyone noticed. Throttle to one ping/day (morning).
        if not dry_run and datetime.now().hour < 12:
            notify_telegram(
                "🚨 BCW social: content bank is EMPTY — posting has STOPPED. "
                "No posts will go out until a new batch is generated. "
                "Ask Claude to draft + load a new batch ASAP."
            )
        sys.exit(1)

    if pending <= 15:
        log(f"⚠️  Only {pending} posts remaining — generate more soon!")
        # Early warning while there's still runway (once/day, morning).
        if not dry_run and pending <= 10 and datetime.now().hour < 12:
            notify_telegram(
                f"📭 BCW social: only {pending} posts left in the bank "
                f"(~{pending // 3} days). Ask Claude to draft a new batch soon."
            )

    # Get next post
    post = get_next_post(bank)
    if not post:
        log("❌ No pending posts found.")
        sys.exit(1)

    status_label = "✅ approved" if post.get("status") == "approved" else "⏳ pending (not reviewed)"
    log(f"📝 Posting: '{post['topic']}' (pillar: {post['pillar']}, status: {status_label})")

    # Get account IDs
    accounts = get_accounts(bank)

    # Step 1: Pick or generate image
    from image_picker import pick as pick_image
    image_type = post.get("image_type", "ai")
    used_log = get_used_log(bank, image_type)
    topic = post.get("topic", "")

    # --- Pre-rendered image bypass -------------------------------------------
    # Some posts ship a ready-made image (e.g. Pillow-rendered review cards) and
    # must NOT go through Kie AI (which would garble verbatim review text).
    # If `prerendered_image` points to a local file, upload it directly and post.
    prerendered = post.get("prerendered_image")
    if prerendered:
        prerendered_path = prerendered
        if not os.path.isabs(prerendered_path):
            prerendered_path = os.path.join(os.path.dirname(__file__), prerendered_path)
        if os.path.exists(prerendered_path):
            log(f"🖼  Using pre-rendered image (no AI): {os.path.basename(prerendered_path)}")
            if dry_run:
                dry_run_display(post, prerendered_path)
                log("\n✅ Dry run complete. No posts published.")
                return
            from zernio_client import ZernioClient
            zernio = ZernioClient()
            media_url = None
            # Retry the upload — a single flaky catbox response stripped the
            # image off the 2026-07-28 review-card post. 3 attempts, backoff.
            for attempt in range(1, 4):
                try:
                    media_url = zernio.upload_image_for_kie(prerendered_path)
                    log(f"🖼  Permanent image URL: {media_url}")
                    break
                except Exception as e:
                    if attempt < 3:
                        log(f"  ⏳ Upload attempt {attempt} failed ({e}) — retrying in {attempt * 5}s")
                        time.sleep(attempt * 5)
                    else:
                        log(f"  ⚠️  Pre-rendered upload failed after 3 attempts: {e}. Posting without image.")
                        notify_telegram(
                            f"⚠️ BCW social: image upload failed for {post.get('id','?')} "
                            f"— posted WITHOUT its image. Attach manually: {prerendered}"
                        )
            log("🚀 Publishing to social platforms...")
            post_to_platforms(post, accounts, media_url, dry_run=False)
            post["status"] = "sent"
            post["sent_at"] = datetime.now(timezone.utc).isoformat()
            post["image_url_used"] = media_url
            save_content_bank(bank)
            log(f"\n✅ Posted (pre-rendered): '{post['topic']}'")
            log(f"   Pending posts remaining: {count_pending(bank)}")
            return
        else:
            log(f"  ⚠️  prerendered_image not found at {prerendered_path}; falling back to normal flow.")

    log(f"🖼  Image type: {image_type}")
    # Derive the catalogue-style image_hint. infer_image_hint() trusts an
    # explicit post['image_hint'] if present, else routes by pillar + topic
    # (personal→Wes, local→van, testimonial→review card, etc.).
    from image_picker import infer_image_hint
    image_hint = infer_image_hint(post)
    log(f"🎯 Image hint: {image_hint}")

    real_image_path = pick_image(image_type, used_log, topic, image_hint=image_hint)

    if dry_run:
        dry_run_display(post, real_image_path)
        # Still show credit balance
        try:
            from higgsfield_client import HiggsfieldClient
            credits = HiggsfieldClient().check_credits()
            log(f"💳 Higgsfield credits: {credits}")
        except Exception:
            pass
        log("\n✅ Dry run complete. No posts published.")
        return

    # Step 2: SAFEGUARD — brand/work posts (show Wes / real jobs) must have a
    # real photo base. Never let the model invent a person from scratch.
    from zernio_client import ZernioClient
    zernio = ZernioClient()
    if real_image_path is None and image_type in ("brand", "work"):
        log("  🛑 No real photo available for a brand/work post — publishing text-only.")
        post_to_platforms(post, accounts, None, dry_run=False)
        post["status"] = "sent"
        post["sent_at"] = datetime.now(timezone.utc).isoformat()
        post["image_url_used"] = None
        save_content_bank(bank)
        log(f"\n✅ Posted: '{post['topic']}' (text only — no base photo)")
        log(f"   Pending posts remaining: {count_pending(bank)}")
        return

    # Step 3: Generate image via Higgsfield (GPT Image 2, annual plan).
    # The CLI takes the LOCAL photo path directly — no pre-upload needed.
    log(f"🎨 Generating image via Higgsfield (base={'yes' if real_image_path else 'no'})...")
    from higgsfield_client import HiggsfieldClient
    higgs = HiggsfieldClient()
    try:
        gen_image_url = higgs.generate_image(
            prompt=post["image_prompt"],
            image_input_path=real_image_path,
            aspect_ratio="1:1",
        )
        log(f"  ✅ Image generated: {gen_image_url[:60]}...")
    except Exception as e:
        log(f"  ❌ Higgsfield image generation failed: {e}")
        gen_image_url = None
        # FALLBACK: post the real base photo as-is (no caption overlay).
        # A real photo beats no image — and Instagram HARD-FAILS without an
        # image, so 'proceeding without image' silently blacked out IG for
        # 12 days when Kie credits ran out (May 30 – Jun 11 2026). Never again.
        if real_image_path:
            log("  🔄 FALLBACK: posting the real base photo without overlay.")
            try:
                gen_image_url = zernio.upload_image_for_kie(real_image_path)
            except Exception as e2:
                log(f"  ⚠️  Fallback upload also failed: {e2}")
        else:
            log("  Proceeding without image (no base photo available)...")
        notify_telegram(
            f"⚠️ BCW social: Higgsfield image generation FAILED for "
            f"{post.get('id','?')} ({str(e)[:120]}). "
            + ("Posted real photo without overlay." if gen_image_url
               else "Posted TEXT-ONLY — Instagram will fail.")
        )
    kie_image_url = gen_image_url  # downstream variable name kept

    # Step 4: Rehost Kie AI image to catbox.moe for a permanent URL.
    # Kie AI URLs (tempfile.aiquickdraw.com) expire quickly — posting to
    # multiple platforms sequentially can cause 409/400 errors on later calls.
    # catbox.moe gives us a permanent URL that works for all platforms.
    media_url = None
    if kie_image_url:
        log("📤 Rehosting Kie AI image to catbox.moe for permanent URL...")
        try:
            media_url = zernio.rehost_url_to_catbox(kie_image_url)
            log(f"🖼  Permanent image URL: {media_url}")
        except Exception as e:
            log(f"  ⚠️  Rehost failed: {e}. Falling back to Kie AI URL directly.")
            media_url = kie_image_url
            log(f"🖼  Using Kie AI image URL: {media_url[:60]}...")

    # Step 5: Post to all 3 platforms
    log("🚀 Publishing to social platforms...")
    post_to_platforms(post, accounts, media_url, dry_run=False)

    # Step 6: Mark as sent + update used image log
    post["status"] = "sent"
    post["sent_at"] = datetime.now(timezone.utc).isoformat()
    post["image_url_used"] = kie_image_url

    if real_image_path:
        update_used_log(bank, image_type, real_image_path)

    save_content_bank(bank)

    # Step 7: Log summary
    remaining = count_pending(bank)
    credits_remaining = "?"
    try:
        credits_remaining = higgs.check_credits()
    except Exception:
        pass

    log(f"\n✅ Posted: '{post['topic']}'")
    log(f"   Image: {os.path.basename(real_image_path) if real_image_path else 'AI generated'}")
    log(f"   Pending posts remaining: {remaining}")
    log(f"   Higgsfield credits remaining: {credits_remaining}")

    # Ops alerts — once per condition per day (08:07 run only) to avoid spam
    is_morning_run = datetime.now().hour < 12
    if isinstance(credits_remaining, (int, float)) and credits_remaining < 50 and is_morning_run:
        notify_telegram(
            f"💳 BCW social: Kie AI credits LOW ({credits_remaining}). "
            f"Top up at higgsfield.ai or images stop generating (Instagram fails without an image)."
        )
    if remaining <= 5:
        log(f"\n⚠️  LOW CONTENT BANK: only {remaining} posts left!")
        log("   Generate more: use the social-posts Claude skill")
        log("   Then run: python social/generate_posts.py <output.json>")
        if is_morning_run:
            notify_telegram(
                f"📭 BCW social: content bank low — {remaining} posts left. "
                f"Ask Claude to generate a new batch."
            )


if __name__ == "__main__":
    main()
