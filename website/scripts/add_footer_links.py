#!/usr/bin/env python3
"""
Add Privacy Policy and Terms links to all HTML page footers.
"""

import os
import re
from pathlib import Path

# Define the root directory
SITE_DIR = Path(__file__).parent.parent / "site"

# Old footer pattern (without privacy/terms links)
OLD_FOOTER_PATTERN = r'<p>© 2026 Better Call Wes\. All rights reserved\.</p>'

# New footer text (with privacy/terms links)
NEW_FOOTER = '<p>© 2026 Better Call Wes. All rights reserved. | <a href="privacy-policy.html" style="color: rgba(255, 255, 255, 0.6);">Privacy Policy</a> | <a href="terms.html" style="color: rgba(255, 255, 255, 0.6);">Terms of Service</a></p>'

# For service pages and location pages (subdirectories), use ../ for relative paths
NEW_FOOTER_SUBDIR = '<p>© 2026 Better Call Wes. All rights reserved. | <a href="../privacy-policy.html" style="color: rgba(255, 255, 255, 0.6);">Privacy Policy</a> | <a href="../terms.html" style="color: rgba(255, 255, 255, 0.6);">Terms of Service</a></p>'

def update_footer(file_path: Path):
    """Update the footer in a single HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has privacy policy link
        if 'Privacy Policy</a>' in content:
            print(f"✓ Already updated: {file_path.relative_to(SITE_DIR)}")
            return False

        # Determine if this is a subdirectory file
        relative_path = file_path.relative_to(SITE_DIR)
        is_subdir = len(relative_path.parts) > 1 and relative_path.parts[0] in ['services', 'locations']

        # Choose the appropriate footer
        new_footer = NEW_FOOTER_SUBDIR if is_subdir else NEW_FOOTER

        # Replace the old footer pattern
        new_content = re.sub(OLD_FOOTER_PATTERN, new_footer, content)

        # Check if any changes were made
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Updated: {file_path.relative_to(SITE_DIR)}")
            return True
        else:
            print(f"⚠ No match found: {file_path.relative_to(SITE_DIR)}")
            return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Find and update all HTML files."""
    print(f"Searching for HTML files in: {SITE_DIR}")

    # Find all HTML files
    html_files = list(SITE_DIR.rglob("*.html"))

    # Exclude the privacy policy and terms pages themselves
    html_files = [f for f in html_files if f.name not in ['privacy-policy.html', 'terms.html']]

    print(f"Found {len(html_files)} HTML files to check\n")

    updated_count = 0
    for html_file in sorted(html_files):
        if update_footer(html_file):
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"Updated {updated_count} of {len(html_files)} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
