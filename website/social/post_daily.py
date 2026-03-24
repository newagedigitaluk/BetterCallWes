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
        try:
            result = client.create_post(
                content=content,
                platform=platform,
                account_id=account_id,
                media_url=media_url,
            )
            results[platform] = result.get("id", "posted")
            log(f"  ✅ {platform.capitalize()}: posted successfully")
        except Exception as e:
            log(f"  ❌ {platform.capitalize()} failed: {e}")
            results[platform] = f"ERROR: {e}"

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
        sys.exit(1)

    if pending <= 5:
        log(f"⚠️  Only {pending} posts remaining — generate more soon!")

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

    log(f"🖼  Image type: {image_type}")
    real_image_path = pick_image(image_type, used_log, topic)

    if dry_run:
        dry_run_display(post, real_image_path)
        # Still show credit balance
        try:
            from kie_client import KieClient
            credits = KieClient().check_credits()
            log(f"💳 Kie AI credits: {credits}")
        except Exception:
            pass
        log("\n✅ Dry run complete. No posts published.")
        return

    # Step 2: Get public URL for real photo (needed as Kie AI image_input)
    # Upload local file to catbox.moe (free, no auth) to get a public URL
    from zernio_client import ZernioClient
    zernio = ZernioClient()
    base_image_url = None
    if real_image_path:
        log(f"📤 Uploading base photo for Kie AI: {os.path.basename(real_image_path)}")
        try:
            base_image_url = zernio.upload_image_for_kie(real_image_path)
        except Exception as e:
            log(f"  ⚠️  Failed to upload base photo: {e}. Will generate pure AI image.")
            base_image_url = None

    # Step 3: Generate image via Kie AI
    log(f"🎨 Generating image via Kie AI (base={'yes' if base_image_url else 'no'})...")
    from kie_client import KieClient
    kie = KieClient()
    try:
        kie_image_url = kie.generate_image(
            prompt=post["image_prompt"],
            image_input_url=base_image_url,
            aspect_ratio="1:1",
        )
        log(f"  ✅ Image generated: {kie_image_url[:60]}...")
    except Exception as e:
        log(f"  ❌ Kie AI image generation failed: {e}")
        log("  Proceeding without image...")
        kie_image_url = None

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
        credits_remaining = kie.check_credits()
    except Exception:
        pass

    log(f"\n✅ Posted: '{post['topic']}'")
    log(f"   Image: {os.path.basename(real_image_path) if real_image_path else 'AI generated'}")
    log(f"   Pending posts remaining: {remaining}")
    log(f"   Kie AI credits remaining: {credits_remaining}")

    if remaining <= 5:
        log(f"\n⚠️  LOW CONTENT BANK: only {remaining} posts left!")
        log("   Generate more: use the social-posts Claude skill")
        log("   Then run: python social/generate_posts.py <output.json>")


if __name__ == "__main__":
    main()
