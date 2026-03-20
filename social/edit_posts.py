"""
Edit and improve pending posts before approval.

Opens each post's content in your terminal editor (nano by default,
or set $EDITOR to use a different one). Edit any field, save, and
the changes are written back to content_bank.json immediately.

Usage:
  python social/edit_posts.py                  # Edit all pending posts
  python social/edit_posts.py --id post_005    # Jump straight to a specific post
  python social/edit_posts.py --approved       # Edit already-approved posts
  python social/edit_posts.py --all            # Edit pending + approved together
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_BANK_PATH = PROJECT_ROOT / "social" / "content_bank.json"

EDITOR = os.environ.get("EDITOR", "nano")

EDITABLE_FIELDS = [
    ("facebook",       "Facebook"),
    ("instagram",      "Instagram"),
    ("twitter",        "Twitter"),
    ("googlebusiness", "Google Business"),
    ("caption",        "Image caption (overlay text)"),
    ("image_prompt",   "Image prompt (Kie AI)"),
    ("topic",          "Topic / title"),
]


def load_bank() -> dict:
    if not CONTENT_BANK_PATH.exists():
        print("❌ content_bank.json not found.")
        sys.exit(1)
    with open(CONTENT_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bank(bank: dict):
    with open(CONTENT_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)


def divider(char="=", width=64):
    print(char * width)


def open_in_editor(field_name: str, current_value: str) -> str:
    """
    Write current_value to a temp file, open in $EDITOR, return edited text.
    The temp file gets a header comment so the user knows what they're editing.
    """
    header = f"# Editing: {field_name}\n# Save and close to apply. Delete everything to clear the field.\n\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(header + current_value)
        tmp_path = f.name

    subprocess.call([EDITOR, tmp_path])

    with open(tmp_path, "r", encoding="utf-8") as f:
        raw = f.read()
    os.unlink(tmp_path)

    # Strip the header comment lines back out
    lines = raw.split("\n")
    content_lines = [l for l in lines if not l.startswith("# ")]
    # Remove leading blank lines left by the header
    while content_lines and content_lines[0] == "":
        content_lines.pop(0)
    # Remove trailing newline
    result = "\n".join(content_lines).rstrip("\n")
    return result


def show_post(post: dict):
    """Print the full post content."""
    divider()
    print(f"  {post['id']}  |  Pillar: {post['pillar']}  |  Status: {post.get('status', '?')}")
    divider()
    print(f"\n📌 Topic:      {post.get('topic', '')}")
    print(f"🔗 Service:    {post.get('service_url', '')}")
    print(f"🖼  Image type: {post.get('image_type', '')}  |  Caption: {post.get('caption', '')}\n")

    divider("-")
    print("FACEBOOK")
    divider("-")
    print(post.get("facebook", "(none)"))

    print()
    divider("-")
    print("INSTAGRAM")
    divider("-")
    print(post.get("instagram", "(none)"))

    twitter = post.get("twitter", "")
    print()
    divider("-")
    print(f"TWITTER  ({len(twitter)}/260 chars)")
    divider("-")
    print(twitter)

    print()
    divider("-")
    print("GOOGLE BUSINESS")
    divider("-")
    print(post.get("googlebusiness") or post.get("facebook", "(none)"))

    print()
    divider("-")
    print(f"IMAGE PROMPT")
    divider("-")
    print(post.get("image_prompt", "(none)"))
    print()


def edit_post(post: dict, bank: dict) -> bool:
    """
    Interactive edit loop for a single post.
    Returns True to move to next post, False to quit entirely.
    """
    while True:
        show_post(post)

        print("  Edit a field:")
        for i, (key, label) in enumerate(EDITABLE_FIELDS, 1):
            extra = f"  ({len(post.get(key, ''))} chars)" if key == "twitter" else ""
            print(f"    [{i}] {label}{extra}")
        print()
        print("    [a] Approve this post")
        print("    [n] Next post (keep as pending)")
        print("    [d] Delete this post")
        print("    [q] Quit")
        print()

        try:
            choice = input("  Choice: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return False

        # Numeric field selection
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(EDITABLE_FIELDS):
                key, label = EDITABLE_FIELDS[idx]
                current = post.get(key, "")
                print(f"\n  Opening {label} in {EDITOR}...\n")
                new_value = open_in_editor(label, current)

                if new_value == current:
                    print("  (No changes made.)\n")
                else:
                    post[key] = new_value
                    post["edited_at"] = datetime.now().isoformat()
                    save_bank(bank)
                    if key == "twitter":
                        print(f"  ✏️  Saved. Twitter is now {len(new_value)}/260 chars.\n")
                    else:
                        print(f"  ✏️  Saved.\n")
            else:
                print("  Invalid number.\n")

        elif choice == "a":
            post["status"] = "approved"
            post["approved_at"] = datetime.now().isoformat()
            save_bank(bank)
            print(f"  ✅ Approved: {post['id']}\n")
            return True  # move to next

        elif choice == "n":
            print(f"  ⏭️  Skipped: {post['id']}\n")
            return True  # move to next

        elif choice == "d":
            confirm = input(f"  Delete {post['id']} permanently? (y/N): ").strip().lower()
            if confirm == "y":
                bank["posts"].remove(post)
                save_bank(bank)
                print(f"  🗑️  Deleted.\n")
                return True
            else:
                print("  Cancelled.\n")

        elif choice == "q":
            return False

        else:
            print("  Please enter a number, a, n, d, or q.\n")


def main():
    args = sys.argv[1:]
    bank = load_bank()

    # Filter posts to work on
    if "--id" in args:
        idx = args.index("--id")
        target_id = args[idx + 1] if idx + 1 < len(args) else None
        posts = [p for p in bank["posts"] if p.get("id") == target_id]
        if not posts:
            print(f"❌ Post '{target_id}' not found.")
            sys.exit(1)
    elif "--approved" in args:
        posts = [p for p in bank["posts"] if p.get("status") == "approved"]
    elif "--all" in args:
        posts = [p for p in bank["posts"] if p.get("status") in ("pending", "approved")]
    else:
        posts = [p for p in bank["posts"] if p.get("status") == "pending"]

    if not posts:
        print("\n  No posts to edit.")
        pending = sum(1 for p in bank["posts"] if p.get("status") == "pending")
        approved = sum(1 for p in bank["posts"] if p.get("status") == "approved")
        print(f"  Pending: {pending}  |  Approved: {approved}")
        return

    print(f"\n  {len(posts)} post(s) to edit. Editor: {EDITOR}")
    print("  (Set $EDITOR environment variable to change editor)\n")

    for post in posts:
        should_continue = edit_post(post, bank)
        if not should_continue:
            break

    # Final summary
    approved = sum(1 for p in bank["posts"] if p.get("status") == "approved")
    pending = sum(1 for p in bank["posts"] if p.get("status") == "pending")
    print(f"  Queue: {approved} approved, {pending} still pending")
    if approved:
        print("  Next post goes live at 8am via cron.")
    else:
        print("  ⚠️  Nothing approved yet — run review_posts.py to approve posts.")


if __name__ == "__main__":
    main()
