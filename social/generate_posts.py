"""
Load Claude skill output into the content bank.

Usage:
  python social/generate_posts.py <skill_output.json>

Where skill_output.json is the JSON array saved from Claude's
social-posts skill output.

The script:
  1. Validates the post structure
  2. Re-sequences IDs to avoid duplicates with existing posts
  3. Sets status = "pending" and sent_at = null
  4. Appends to social/content_bank.json
"""

import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_BANK_PATH = PROJECT_ROOT / "social" / "content_bank.json"

REQUIRED_FIELDS = [
    "id", "pillar", "topic", "service_url",
    "facebook", "instagram", "twitter", "googlebusiness",
    "image_type", "caption", "image_prompt",
]

VALID_IMAGE_TYPES = {"brand", "work", "asset", "ai"}


def load_content_bank() -> dict:
    if CONTENT_BANK_PATH.exists():
        with open(CONTENT_BANK_PATH, "r") as f:
            return json.load(f)
    return {
        "meta": {
            "generated_at": "",
            "accounts": {"facebook": "", "instagram": "", "twitter": ""},
            "used_brand_images": [],
            "used_work_images": [],
            "used_asset_images": [],
        },
        "posts": [],
    }


def save_content_bank(bank: dict):
    with open(CONTENT_BANK_PATH, "w") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)


def validate_post(post: dict, index: int) -> list:
    """Return list of validation errors for a post."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in post:
            errors.append(f"Missing field: '{field}'")

    image_type = post.get("image_type", "")
    if image_type not in VALID_IMAGE_TYPES:
        errors.append(f"Invalid image_type '{image_type}' (must be brand/work/asset/ai)")

    twitter = post.get("twitter", "")
    if len(twitter) > 280:
        errors.append(f"Twitter text is {len(twitter)} chars (max 280)")

    return errors


def get_next_id(existing_posts: list) -> int:
    """Return the next available post number."""
    if not existing_posts:
        return 1
    ids = []
    for p in existing_posts:
        pid = p.get("id", "")
        try:
            ids.append(int(pid.replace("post_", "")))
        except ValueError:
            pass
    return max(ids) + 1 if ids else 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python social/generate_posts.py <skill_output.json>")
        print("\nExample:")
        print("  python social/generate_posts.py social/posts_batch.json")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    # Load input JSON
    with open(input_file, "r", encoding="utf-8") as f:
        try:
            new_posts = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {input_file}: {e}")
            sys.exit(1)

    if not isinstance(new_posts, list):
        print("❌ Expected a JSON array of posts.")
        sys.exit(1)

    print(f"📥 Loaded {len(new_posts)} posts from {input_file.name}")

    # Validate all posts
    validation_errors = False
    for i, post in enumerate(new_posts):
        errors = validate_post(post, i)
        if errors:
            print(f"\n⚠️  Post {i+1} ({post.get('topic', '?')}):")
            for err in errors:
                print(f"   - {err}")
            validation_errors = True

    if validation_errors:
        print("\n⚠️  Validation warnings found. Posts will still be added.")
        print("   Fix warnings if posts won't display correctly.")
        response = input("\nContinue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    # Load content bank
    bank = load_content_bank()
    existing_count = len(bank["posts"])
    next_id = get_next_id(bank["posts"])

    # Process and append posts
    added = 0
    for post in new_posts:
        # Re-sequence ID
        post["id"] = f"post_{next_id:03d}"
        next_id += 1

        # Set tracking fields
        post["status"] = "pending"
        post["sent_at"] = None
        post["image_url_used"] = None

        bank["posts"].append(post)
        added += 1

    # Update metadata
    bank["meta"]["generated_at"] = datetime.utcnow().isoformat()

    # Save
    save_content_bank(bank)

    pending_count = sum(1 for p in bank["posts"] if p.get("status") == "pending")
    print(f"\n✅ Added {added} posts to content bank.")
    print(f"   Total pending: {pending_count} posts")
    print(f"   At 1 post/day, that's {pending_count} days of content.")

    if pending_count <= 5:
        print("\n⚠️  Content bank is running low! Generate more posts soon.")


if __name__ == "__main__":
    main()
