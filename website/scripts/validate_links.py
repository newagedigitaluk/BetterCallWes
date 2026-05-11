"""Validate internal links in website/site/.

Walks every .html file, extracts hrefs and srcs, and checks that each
points at a file (or directory containing index.html) that actually
exists on disk. Externals, anchors, and mailto/tel/wa.me links are
skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "javascript:", "wa.me", "data:", "#")


def main() -> int:
    valid: set[str] = set()
    for f in SITE.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(SITE).as_posix()
        valid.add(rel)

    href_re = re.compile(r'(?:href|src)=["\']([^"\']+)["\']')
    errors: list[str] = []

    for f in SITE.rglob("*.html"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        rel_file = f.relative_to(SITE).as_posix()
        for url in href_re.findall(text):
            if not url or url.startswith(SKIP_PREFIXES):
                continue
            # Strip query and fragment
            clean = url.split("?", 1)[0].split("#", 1)[0]
            if not clean:
                continue
            # Resolve site-absolute paths from SITE root; relative paths from the file's dir.
            base = SITE if clean.startswith("/") else f.parent
            try:
                resolved = (base / clean.lstrip("/")).resolve().relative_to(SITE.resolve()).as_posix()
            except ValueError:
                errors.append(f"{rel_file}: '{url}' resolves outside site")
                continue
            # Exact file match
            if resolved in valid:
                continue
            # Resolves to site root
            if resolved in ("", "."):
                if "index.html" in valid:
                    continue
            # Directory → index.html match
            index_candidate = (resolved.rstrip("/") + "/index.html").lstrip("/")
            if index_candidate in valid:
                continue
            # Clean URL → .html match
            if (resolved + ".html") in valid:
                continue
            errors.append(f"{rel_file}: '{url}' → {resolved}")

    if errors:
        print(f"Broken links: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"All internal links validated successfully. {sum(1 for _ in SITE.rglob('*.html'))} HTML files scanned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
