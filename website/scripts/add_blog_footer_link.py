#!/usr/bin/env python3
"""
Inserts a Blog link into the Quick Links footer of every page that follows
the standard footer pattern (any page containing
'<li><a href="...reviews.html">Reviews</a></li>').

The Blog link is inserted immediately after the Reviews link. Path depth
is handled automatically:
  - top-level pages         -> href="blog/"
  - one-level subdirs       -> href="../blog/"
  - blog/index.html itself  -> skipped (already linked)

Idempotent: if a page already has a Blog footer link, it is skipped.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"

REVIEWS_LI_RE = re.compile(
    r'^(?P<indent>[ \t]*)<li><a href="(?P<prefix>(?:\.\./)*)reviews\.html">Reviews</a></li>[ \t]*\n',
    re.MULTILINE,
)

# Fallback: pages with a stripped Quick Links block (no Reviews link).
# Match the closing </ul> of the Quick Links list. We use the marker
# `<h3>Quick Links</h3>` followed by a `<ul ...>` and then capture
# the indent of the closing </ul>.
QUICK_LINKS_BLOCK_RE = re.compile(
    r'(<h3>Quick Links</h3>\s*<ul[^>]*>.*?)(?P<indent>[ \t]*)</ul>',
    re.DOTALL,
)

# Detect the path-prefix that this page uses for internal links (e.g. ../).
PREFIX_PROBE_RE = re.compile(r'href="(?P<prefix>(?:\.\./)+)index\.html"')

EXISTING_BLOG_RE = re.compile(
    r'<a href="(?:\.\./)*blog/(?:index\.html)?">Blog</a>'
)


def patch_file(path: Path) -> str:
    if path.resolve() == (SITE / "blog" / "index.html").resolve():
        return "skipped-blog-index"

    text = path.read_text(encoding="utf-8")
    if EXISTING_BLOG_RE.search(text):
        return "skipped-already"

    m = REVIEWS_LI_RE.search(text)
    if m:
        indent = m.group("indent")
        prefix = m.group("prefix")
        insertion = f'{indent}<li><a href="{prefix}blog/">Blog</a></li>\n'
        new_text = text[: m.end()] + insertion + text[m.end():]
        path.write_text(new_text, encoding="utf-8")
        return "patched"

    # Fallback path: pages whose Quick Links block has no Reviews link.
    block = QUICK_LINKS_BLOCK_RE.search(text)
    if not block:
        return "skipped-no-quick-links"

    # Figure out the relative prefix for the page (../ for subdirs, '' for root).
    prefix_match = PREFIX_PROBE_RE.search(text)
    prefix = prefix_match.group("prefix") if prefix_match else ""
    indent = block.group("indent")
    li_indent = indent + " "
    insertion = f'{li_indent}<li><a href="{prefix}blog/">Blog</a></li>\n'
    # Insert just before the closing </ul>.
    end_pos = block.end() - len(indent) - len("</ul>")
    new_text = text[:end_pos] + insertion + text[end_pos:]
    path.write_text(new_text, encoding="utf-8")
    return "patched-fallback"


def main() -> int:
    counts = {
        "patched": 0,
        "patched-fallback": 0,
        "skipped-no-quick-links": 0,
        "skipped-already": 0,
        "skipped-blog-index": 0,
    }
    skipped: list[tuple[str, Path]] = []

    for html in sorted(SITE.rglob("*.html")):
        result = patch_file(html)
        counts[result] += 1
        if result.startswith("skipped"):
            skipped.append((result, html))

    print("=== Blog footer link sweep ===")
    for key, value in counts.items():
        print(f"  {key}: {value}")

    if skipped:
        print("\nSkipped files:")
        for result, path in skipped:
            print(f"  [{result}] {path.relative_to(SITE)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
