#!/usr/bin/env python3
"""Render a page in headless Chrome and report what actually broke.

Written after the /s/<token> scheduling page shipped broken twice. curl
said every asset was fine because curl was asked for /js/schedule.js
directly; the browser, resolving relative paths against /s/, asked for
/s/js/schedule.js and got a 404. The page then sat on its loading state
forever. Fetching URLs you construct yourself cannot catch that. Only
resolving them the way a browser does can.

Usage:
    python check_page_renders.py <url> [--expect-absent "Loading"] ...
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin

CHROME = "google-chrome"
ASSET_RE = re.compile(r'(?:src|href)="([^"]+)"')
SKIP = ("data:", "mailto:", "tel:", "javascript:", "#")
# preconnect/dns-prefetch point at an origin, not a file. Fetching them
# returns 404 from most CDNs and means nothing.
HINT_RE = re.compile(r'<link[^>]*rel="(?:preconnect|dns-prefetch)"[^>]*>', re.I)
# Text inside hidden="" is not on screen. Matching it made a page that had
# already moved to its error state look like it was still loading.
HIDDEN_RE = re.compile(r'<(\w+)[^>]*\shidden(?:="")?[^>]*>.*?</\1>', re.S | re.I)


def render(url: str, budget_ms: int = 15000) -> str:
    out = subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         f"--virtual-time-budget={budget_ms}", "--dump-dom", url],
        capture_output=True, text=True, timeout=budget_ms / 1000 + 30,
    )
    return out.stdout


def check_assets(url: str, html: str) -> list[tuple[str, str]]:
    """Resolve every asset the way the browser does, from the page URL."""
    bad = []
    for ref in dict.fromkeys(ASSET_RE.findall(html)):
        if ref.startswith(SKIP):
            continue
        target = urljoin(url, ref)
        try:
            req = urllib.request.Request(target, method="GET")
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status >= 400:
                    bad.append((ref, str(r.status)))
        except urllib.error.HTTPError as e:
            bad.append((ref, str(e.code)))
        except Exception as e:  # noqa: BLE001
            bad.append((ref, type(e).__name__))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--expect-absent", action="append", default=[],
                    help="text that must NOT be visible once rendered")
    ap.add_argument("--expect-present", action="append", default=[])
    args = ap.parse_args()

    html = render(args.url)
    visible = HIDDEN_RE.sub(" ", html)
    if not html.strip():
        print("FAIL: chrome returned nothing")
        return 1

    failures = []
    for ref, code in check_assets(args.url, HINT_RE.sub(" ", html)):
        failures.append(f"asset {ref} -> {code} (resolved from the page URL)")
    for text in args.expect_absent:
        if text in visible:
            failures.append(f"still showing {text!r} after JS ran")
    for text in args.expect_present:
        if text not in visible:
            failures.append(f"missing {text!r} after JS ran")

    if failures:
        print(f"FAIL {args.url}")
        for f in failures:
            print("  -", f)
        return 1
    print(f"OK {args.url} ({len(html)} bytes rendered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
