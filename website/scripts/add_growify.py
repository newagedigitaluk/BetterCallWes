"""
Add Growify pixel to all HTML pages and wire up WhatsApp button click
as a Growify conversion event.

- Pixel script injected into <head> of every page
- Conversion event fires on any WhatsApp button/link click
"""

import os
import re
from pathlib import Path

WEBSITE_DIR = Path(__file__).parent.parent.parent / "Website"

GROWIFY_PIXEL = """    <!-- Growify Pixel -->
    <script
        src="https://cdn.growify.ai/pixel.min.js"
        data-website-id="b1da141995f354578b374c1c1ce45287:f1a6af4ef5e14a02766e2e7a3d1eb1f18b3747e02f785abec67091bc988276db9726d52ebb3f4a61f998aff8c550d978"
        data-endpoint="api_v2"
        data-platform="web"
    ></script>"""

# Conversion event — fires on WhatsApp link click
# Adapted for a service business (no products/orders)
GROWIFY_CONVERSION_SCRIPT = """
    <!-- Growify WhatsApp Conversion Event -->
    <script>
      document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('a[href*="wa.me"], a[href*="whatsapp"]').forEach(function (el) {
          el.addEventListener('click', function () {
            window.grpQueue = window.grpQueue || [];
            if (!window.grp) {
              window.grp = function () { window.grpQueue.push(arguments); };
            }
            var service = document.title.replace(' | Better Call Wes', '').trim();
            window.grp('conversion', {
              orderId: 'WA-' + Date.now(),
              products: [{
                productId: 'whatsapp-enquiry',
                productName: service || 'Plumbing & Heating Enquiry',
                productPrice: 0,
                productBrand: 'Better Call Wes',
                productQuantity: 1,
                purchaseValue: 0
              }]
            });
          });
        });
      });
    </script>"""


def already_has_growify(content):
    return "growify.ai" in content


def add_pixel(content):
    """Inject pixel script just before </head>."""
    return re.sub(
        r"(</head>)",
        GROWIFY_PIXEL + "\n\\1",
        content,
        count=1,
        flags=re.IGNORECASE,
    )


def add_conversion(content):
    """Inject conversion script just before </body>."""
    return re.sub(
        r"(</body>)",
        GROWIFY_CONVERSION_SCRIPT + "\n\\1",
        content,
        count=1,
        flags=re.IGNORECASE,
    )


def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if already_has_growify(content):
        return "skip"

    content = add_pixel(content)
    content = add_conversion(content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return "done"


def main():
    html_files = list(WEBSITE_DIR.rglob("*.html"))
    # Skip the roplumb subfolder (template files)
    html_files = [f for f in html_files if "roplumb" not in str(f)]

    done = skip = error = 0
    for path in sorted(html_files):
        try:
            result = process_file(path)
            if result == "done":
                done += 1
                print(f"  ✅ {path.relative_to(WEBSITE_DIR)}")
            else:
                skip += 1
                print(f"  ⏭  {path.relative_to(WEBSITE_DIR)} (already has Growify)")
        except Exception as e:
            error += 1
            print(f"  ❌ {path.relative_to(WEBSITE_DIR)} — {e}")

    print(f"\nDone: {done}  Skipped: {skip}  Errors: {error}")


if __name__ == "__main__":
    main()
