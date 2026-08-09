"""
Create per-post Linke short links for every post in content_bank.json that
has a `short_link_slug` but no `short_link` yet.

Reads the slug from each post, creates a Linke short link inside the
"Better Call Wes" folder using the BCW custom domain (u.bettercallwes.co.uk),
and writes the resulting URL back into the post as `short_link`.

Idempotent — skips posts that already have a `short_link`. Re-runnable.

Usage:
    LINKE_API_KEY=... python3 website/social/create_post_links.py [--dry-run]

Rate limit: Linke allows 500 requests/day. With ~90 posts plus a brief pause
between calls, this runs in ~30 seconds and uses ~90 of the daily quota.
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
BANK_PATH = PROJECT_ROOT / "website" / "social" / "content_bank.json"

sys.path.insert(0, str(PROJECT_ROOT / "website" / "social"))
from linke_client import LinkeClient


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🔍 DRY RUN — no links will be created\n")

    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    posts = bank.get("posts", [])

    # Find posts needing a short link.
    # Only PENDING posts — creating links for already-sent posts is wasted
    # quota, since those went out with the generic service link baked in.
    needs_link = [
        p for p in posts
        if p.get("short_link_slug")
        and not p.get("short_link")
        and p.get("status") in ("pending", "approved")
    ]
    print(f"📊 Posts in bank: {len(posts)}")
    print(f"📊 Posts needing a per-post short link: {len(needs_link)}")
    if not needs_link:
        print("✅ Nothing to do — all posts with slugs already have short links.")
        return

    if dry_run:
        for p in needs_link[:10]:
            print(f"  would create: {p.get('short_link_slug'):28s} → {p.get('service_url','')[:60]}")
        if len(needs_link) > 10:
            print(f"  ... and {len(needs_link) - 10} more")
        return

    client = LinkeClient()
    generic_shorts = bank.get("meta", {}).get("generic_short_links", {})
    if not generic_shorts:
        print("⚠️  No generic_short_links in meta — skipping URL swap step.")
    created = 0
    swapped = 0
    failed = []

    for post in needs_link:
        slug = post["short_link_slug"]
        original = post["service_url"]
        topic = (post.get("topic") or "")[:60]
        try:
            result = client.create_short_link(
                url=original,
                name=slug,
                folder="Better Call Wes",
                title=f"BCW post {post.get('id','?')} — {topic}",
            )
            short_url = result.get("data", {}).get("short_link")
            if not short_url:
                raise RuntimeError(f"No short_link in response: {result}")
            post["short_link"] = short_url
            created += 1
            print(f"  ✅ {slug:28s} → {short_url}")

            # Swap the generic short URL in each platform's text with the per-post URL.
            # This is what enables per-post click attribution.
            service_slug = post.get("service_slug")
            if service_slug and generic_shorts.get(service_slug):
                generic_url = generic_shorts[service_slug]
                for platform in ("facebook", "twitter", "googlebusiness"):
                    body = post.get(platform, "")
                    if generic_url in body:
                        post[platform] = body.replace(generic_url, short_url)
                        swapped += 1

            time.sleep(0.3)  # be polite
        except Exception as e:
            failed.append((slug, str(e)))
            print(f"  ❌ {slug:28s} → {e}")

    # Save the updated bank
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 Saved {created} new short_link URLs to content_bank.json")
    print(f"   Swapped generic→per-post URLs in {swapped} platform text fields")

    if failed:
        print(f"\n⚠️  {len(failed)} failures:")
        for slug, err in failed:
            print(f"   {slug}: {err}")


if __name__ == "__main__":
    main()
