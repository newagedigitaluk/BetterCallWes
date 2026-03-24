"""
One-time setup script for the Better Call Wes social posting system.

What this does:
  1. Converts all HEIC/HEIF photos in Brand Images/Work Images/ → JPG
     (so they can be used as image inputs by Kie AI)
  2. Lists all connected Zernio social accounts
  3. Prompts you to identify the Facebook, Instagram, and Twitter account IDs
  4. Saves those IDs to social/content_bank.json

Run once before using post_daily.py:
  python social/setup_accounts.py
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_BANK_PATH = PROJECT_ROOT / "social" / "content_bank.json"
WORK_IMAGES_DIR = PROJECT_ROOT / "Brand Images" / "Work Images"
BRAND_IMAGES_DIR = PROJECT_ROOT / "Brand Images"


def convert_heic_files():
    """Convert all HEIC/HEIF files in the Work Images folder to JPG."""
    try:
        import pillow_heif
        from PIL import Image
        pillow_heif.register_heif_opener()
    except ImportError:
        print("⚠️  pillow-heif not installed. Skipping HEIC conversion.")
        print("   Run: pip install pillow-heif")
        return 0

    heic_extensions = {".heic", ".heif"}
    converted = 0
    errors = 0

    for directory in [WORK_IMAGES_DIR, BRAND_IMAGES_DIR]:
        if not directory.exists():
            continue
        for file_path in directory.iterdir():
            if file_path.suffix.lower() in heic_extensions:
                jpg_path = file_path.with_suffix(".jpg")
                if jpg_path.exists():
                    continue  # Already converted
                try:
                    img = Image.open(file_path)
                    img = img.convert("RGB")
                    img.save(jpg_path, "JPEG", quality=92)
                    converted += 1
                    print(f"  ✓ {file_path.name} → {jpg_path.name}")
                except Exception as e:
                    errors += 1
                    print(f"  ✗ Failed to convert {file_path.name}: {e}")

    if converted > 0:
        print(f"\n✅ Converted {converted} HEIC file(s) to JPG.")
    else:
        print("✅ No HEIC files to convert (already done or none found).")

    if errors > 0:
        print(f"⚠️  {errors} file(s) failed to convert.")

    return converted


def list_zernio_accounts():
    """List all connected Zernio accounts and return them."""
    sys.path.insert(0, str(PROJECT_ROOT / "social"))
    from zernio_client import ZernioClient

    print("\n🔍 Fetching connected Zernio accounts...")
    try:
        client = ZernioClient()
        accounts = client.list_accounts()
    except Exception as e:
        print(f"❌ Failed to connect to Zernio: {e}")
        print("   Check that ZERNIO_API_KEY is set correctly.")
        sys.exit(1)

    if not accounts:
        print("❌ No social accounts connected to your Zernio account.")
        print("   Connect your accounts at: https://zernio.com/dashboard")
        sys.exit(1)

    print(f"\n{'#':<4} {'Platform':<20} {'Account ID'}")
    print("-" * 55)
    for i, acc in enumerate(accounts, 1):
        platform = acc.get("platform", "Unknown")
        acc_id = acc.get("id", "?")
        print(f"{i:<4} {platform:<20} {acc_id}")

    return accounts


def prompt_for_account_ids(accounts: list) -> dict:
    """Ask user to identify which account ID belongs to each platform."""
    platform_ids = {"facebook": "", "instagram": "", "twitter": ""}

    print("\n📋 Please enter the account IDs for each platform.")
    print("   (Copy from the table above — or press Enter to skip a platform)\n")

    for platform in ["facebook", "instagram", "twitter"]:
        # Check if any account in the list matches this platform
        matches = [
            a for a in accounts
            if a.get("platform", "").lower() == platform
        ]

        if len(matches) == 1:
            # Auto-select if there's exactly one match
            acc_id = matches[0]["id"]
            print(f"  ✅ {platform.capitalize()} account auto-detected: {acc_id}")
            platform_ids[platform] = acc_id
        else:
            value = input(f"  Enter {platform.capitalize()} account ID: ").strip()
            if value:
                platform_ids[platform] = value

    return platform_ids


def save_to_content_bank(account_ids: dict):
    """Save account IDs to content_bank.json."""
    if CONTENT_BANK_PATH.exists():
        with open(CONTENT_BANK_PATH, "r") as f:
            bank = json.load(f)
    else:
        bank = {
            "meta": {
                "generated_at": "",
                "accounts": {},
                "used_brand_images": [],
                "used_work_images": [],
                "used_asset_images": [],
            },
            "posts": [],
        }

    bank["meta"]["accounts"] = account_ids

    with open(CONTENT_BANK_PATH, "w") as f:
        json.dump(bank, f, indent=2)

    print(f"\n✅ Account IDs saved to {CONTENT_BANK_PATH.name}")


def check_kie_credits():
    """Check and display remaining Kie AI credits."""
    sys.path.insert(0, str(PROJECT_ROOT / "social"))
    try:
        from kie_client import KieClient
        client = KieClient()
        credits = client.check_credits()
        print(f"\n💳 Kie AI credits remaining: {credits}")
    except Exception as e:
        print(f"\n⚠️  Could not check Kie AI credits: {e}")
        print("   Check that KIE_API_KEY is set correctly.")


def main():
    print("=" * 55)
    print("  Better Call Wes — Social Posting Setup")
    print("=" * 55)

    # Step 1: Convert HEIC files
    print("\n📸 Step 1: Converting HEIC photos to JPG...")
    convert_heic_files()

    # Step 2: List Zernio accounts
    print("\n🌐 Step 2: Connecting to Zernio...")
    accounts = list_zernio_accounts()

    # Step 3: Map account IDs
    print("\n🔗 Step 3: Mapping accounts to platforms...")
    account_ids = prompt_for_account_ids(accounts)

    # Step 4: Save to content bank
    save_to_content_bank(account_ids)

    # Step 5: Check Kie AI credits
    print("\n🎨 Step 5: Checking Kie AI credits...")
    check_kie_credits()

    # Summary
    print("\n" + "=" * 55)
    print("  Setup complete! Next steps:")
    print("=" * 55)
    print("\n  1. Ask Claude to generate posts:")
    print('     "Use the social-posts skill to generate 30 posts"')
    print("     Save the JSON output to: social/posts_batch.json")
    print("\n  2. Load posts into the content bank:")
    print("     python social/generate_posts.py social/posts_batch.json")
    print("\n  3. Preview the first post:")
    print("     python social/post_daily.py --dry-run")
    print("\n  4. When ready, add the cron job (see README)")
    print()


if __name__ == "__main__":
    main()
