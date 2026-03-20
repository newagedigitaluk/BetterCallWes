"""
Review and approve pending posts before they go live.

Usage:
  python social/review_posts.py          # Interactive review — approve/skip posts
  python social/review_posts.py --list   # Quick summary of all pending posts
  python social/review_posts.py --reset  # Reset all approved posts back to pending

How it works:
  - Posts sit as 'pending' after generate_posts.py loads them
  - This script lets you review each post and mark it 'approved'
  - post_daily.py only publishes 'approved' posts
  - Skip a post to leave it pending for next review session
"""

import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_BANK_PATH = PROJECT_ROOT / "social" / "content_bank.json"


def load_bank() -> dict:
    if not CONTENT_BANK_PATH.exists():
        print("❌ content_bank.json not found. Run setup_accounts.py first.")
        sys.exit(1)
    with open(CONTENT_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bank(bank: dict):
    with open(CONTENT_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)


def print_divider(char="=", width=64):
    print(char * width)


def print_post(post: dict, index: int, total: int):
    """Display a single post for review."""
    print_divider()
    print(f"  Post {index}/{total}  |  ID: {post['id']}  |  Pillar: {post['pillar']}")
    print_divider()
    print(f"\n📌 Topic:      {post['topic']}")
    print(f"🔗 Service:    {post.get('service_url', 'N/A')}")
    print(f"🖼  Image type: {post.get('image_type', 'N/A')}")
    print(f"💬 Caption:    {post.get('caption', 'N/A')}\n")

    print_divider("-")
    print("FACEBOOK")
    print_divider("-")
    print(post.get("facebook", "(none)"))

    print()
    print_divider("-")
    print("INSTAGRAM")
    print_divider("-")
    print(post.get("instagram", "(none)"))

    print()
    print_divider("-")
    print(f"TWITTER  ({len(post.get('twitter', ''))} chars)")
    print_divider("-")
    print(post.get("twitter", "(none)"))

    print()
    print_divider("-")
    print("GOOGLE BUSINESS")
    print_divider("-")
    gb = post.get("googlebusiness") or post.get("facebook", "(none)")
    print(gb)

    print()
    print_divider("-")
    print(f"IMAGE PROMPT: {post.get('image_prompt', 'N/A')[:120]}{'...' if len(post.get('image_prompt', '')) > 120 else ''}")
    print()


def list_posts(bank: dict):
    """Print a quick summary table of all pending + approved posts."""
    pending = [p for p in bank["posts"] if p.get("status") == "pending"]
    approved = [p for p in bank["posts"] if p.get("status") == "approved"]
    sent = [p for p in bank["posts"] if p.get("status") == "sent"]

    print(f"\n{'ID':<12} {'STATUS':<10} {'PILLAR':<14} TOPIC")
    print_divider("-")
    for p in approved:
        print(f"  {p['id']:<10} {'✅ approved':<10} {p['pillar']:<14} {p['topic']}")
    for p in pending:
        print(f"  {p['id']:<10} {'⏳ pending':<10} {p['pillar']:<14} {p['topic']}")

    print()
    print(f"  ✅ Approved (ready to post): {len(approved)}")
    print(f"  ⏳ Pending (needs review):   {len(pending)}")
    print(f"  📤 Already sent:             {len(sent)}")
    print()

    if not approved and not pending:
        print("  Content bank is empty. Generate more posts with the social-posts skill.")


def interactive_review(bank: dict):
    """Walk through pending posts one by one for approval."""
    pending = [p for p in bank["posts"] if p.get("status") == "pending"]

    if not pending:
        approved = sum(1 for p in bank["posts"] if p.get("status") == "approved")
        print(f"\n✅ No pending posts to review.")
        if approved:
            print(f"   {approved} posts already approved and queued to post.")
        else:
            print("   Generate more: use the social-posts Claude skill, then run generate_posts.py")
        return

    print(f"\n📋 {len(pending)} posts to review.\n")
    print("  Commands:  [a] Approve   [s] Skip   [e] Edit caption   [d] Delete   [q] Quit\n")

    approved_count = 0
    skipped_count = 0
    i = 0

    while i < len(pending):
        post = pending[i]
        print_post(post, i + 1, len(pending))

        while True:
            try:
                choice = input("  Action [a/s/e/d/q]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                choice = "q"

            if choice == "a":
                post["status"] = "approved"
                post["approved_at"] = datetime.now().isoformat()
                save_bank(bank)
                print(f"  ✅ Approved: {post['id']}\n")
                approved_count += 1
                break

            elif choice == "s":
                print(f"  ⏭️  Skipped: {post['id']}\n")
                skipped_count += 1
                break

            elif choice == "e":
                print(f"  Current caption: {post.get('caption', '')}")
                new_caption = input("  New caption (Enter to keep): ").strip()
                if new_caption:
                    post["caption"] = new_caption
                    save_bank(bank)
                    print(f"  ✏️  Caption updated.")
                # Re-show the post with updated caption
                print_post(post, i + 1, len(pending))

            elif choice == "d":
                confirm = input(f"  Delete {post['id']} permanently? (y/N): ").strip().lower()
                if confirm == "y":
                    bank["posts"].remove(post)
                    save_bank(bank)
                    print(f"  🗑️  Deleted: {post['id']}\n")
                    pending.remove(post)
                    i -= 1  # Don't advance — next post is now at same index
                break

            elif choice == "q":
                print(f"\n  Exiting review. Approved {approved_count}, skipped {skipped_count}.")
                _print_summary(bank)
                return

            else:
                print("  Please enter a, s, e, d, or q.")

        i += 1

    print(f"\n🎉 Review complete.")
    print(f"   Approved this session: {approved_count}")
    print(f"   Skipped: {skipped_count}")
    _print_summary(bank)


def _print_summary(bank: dict):
    approved = sum(1 for p in bank["posts"] if p.get("status") == "approved")
    pending = sum(1 for p in bank["posts"] if p.get("status") == "pending")
    print(f"\n   Queue: {approved} approved, {pending} still pending")
    if approved:
        print(f"   Next post goes live tomorrow at 8am via cron.")
    else:
        print(f"   ⚠️  Nothing approved yet — cron will not post until you approve something.")


def reset_approved(bank: dict):
    """Move all approved posts back to pending."""
    count = 0
    for post in bank["posts"]:
        if post.get("status") == "approved":
            post["status"] = "pending"
            post.pop("approved_at", None)
            count += 1
    save_bank(bank)
    print(f"  ↩️  Reset {count} approved posts back to pending.")


def main():
    args = sys.argv[1:]
    bank = load_bank()

    if "--list" in args or "-l" in args:
        list_posts(bank)
    elif "--reset" in args:
        reset_approved(bank)
    else:
        interactive_review(bank)


if __name__ == "__main__":
    main()
