#!/usr/bin/env python3
"""
Zernio compliance auditor.

Four projects post through Zernio from four separate copies of
zernio_client.py, and they have drifted apart. This checks every copy against
the documented API contract and prints what's wrong, so a docs change or a
copy-paste regression gets caught instead of quietly mis-posting for weeks.

Each rule below traces to a specific page of docs.zernio.com. If a rule fires
on a file, go and read that page before "fixing" the file — the docs are the
authority, not the other copies.

Usage:
  python3 zernio_compliance.py                      # audit every project
  python3 zernio_compliance.py --strict             # exit 1 on any failure
  python3 zernio_compliance.py --only "Better Call Wes" --strict --telegram
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECTS = Path("/home/wes/Coding/Projects")


def find_clients() -> list[Path]:
    return sorted(p for p in PROJECTS.glob("*/**/zernio_client.py")
                  if "node_modules" not in p.parts)


# (id, severity, doc page, predicate(src) -> ok, message)
RULES = [
    (
        "idempotency", "HIGH", "guides/idempotency",
        lambda s: "x-request-id" in s,
        "No x-request-id header. A retried write can double-post; the docs "
        "require a UUIDv4 per logical request.",
    ),
    (
        "media-type-field", "HIGH", "guides/media-uploads",
        lambda s: not re.search(r'"mediaType"\s*:', s),
        'mediaItems uses "mediaType". The documented field is "type" '
        '(image|video|gif|document).',
    ),
    (
        "psd-nesting", "HIGH", "platforms/facebook",
        lambda s: not re.search(r'payload\[\s*["\']platformSpecificData', s),
        "platformSpecificData set at the top level of the payload. It belongs "
        "inside each entry of the platforms array, or it is silently ignored.",
    ),
    (
        "psd-not-keyed", "HIGH", "platforms/facebook",
        lambda s: not re.search(r'platformSpecificData["\']\s*\]?\s*[:=]\s*\{\s*["\'](facebook|instagram)["\']\s*:', s),
        "platformSpecificData keyed by platform name. It is not keyed — the "
        "platform is already known from the entry it sits in.",
    ),
    (
        "fb-settings-alias", "MEDIUM", "platforms/facebook",
        lambda s: "facebookSettings" not in s,
        "Uses facebookSettings. Undocumented; the documented route is "
        "platforms[].platformSpecificData.",
    ),
    (
        "rate-limit", "MEDIUM", "guides/rate-limits",
        lambda s: "429" in s and ("Retry-After" in s or "retryAfterSeconds" in s),
        "429 not handled via Retry-After / details.retryAfterSeconds.",
    ),
    (
        "duplicate-409", "LOW", "guides/idempotency",
        lambda s: "409" in s,
        "409 (content duplicate within 24h) not handled — a benign duplicate "
        "surfaces as a hard failure.",
    ),
    (
        "limits-preflight", "MEDIUM", "platforms/*",
        lambda s: "zernio_limits" in s,
        "No preflight against documented per-platform limits (caption length, "
        "image size/format, video duration, Google Business has no video).",
    ),
]


def audit(path: Path) -> list[tuple]:
    src = path.read_text(encoding="utf-8", errors="replace")
    return [(rid, sev, doc, msg) for rid, sev, doc, ok, msg in RULES if not ok(src)]


def _only_arg() -> str | None:
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def notify(text: str):
    """Telegram alert via the same channel the posting agents use."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from post_daily import notify_telegram
        notify_telegram(text)
    except Exception as e:
        print(f"  (telegram alert failed: {e})")


def main() -> int:
    strict = "--strict" in sys.argv
    only = _only_arg()
    clients = find_clients()
    if only:
        clients = [c for c in clients
                   if c.relative_to(PROJECTS).parts[0] == only]
    if not clients:
        print("No zernio_client.py found.")
        return 0

    total = 0
    for path in clients:
        project = path.relative_to(PROJECTS).parts[0]
        fails = audit(path)
        total += len(fails)
        status = "OK" if not fails else f"{len(fails)} issue(s)"
        print(f"\n{project}  [{status}]")
        print(f"  {path}")
        for rid, sev, doc, msg in fails:
            print(f"    {sev:6} {rid:18} {msg}")
            print(f"    {'':6} {'':18} docs.zernio.com/{doc}")

    print(f"\n{'-'*68}\n{len(clients)} client(s) audited, {total} issue(s) total.")

    if total and "--telegram" in sys.argv:
        scope = only or "all projects"
        notify(f"\u26a0\ufe0f Zernio compliance: {total} issue(s) in {scope}. "
               f"Run website/social/zernio_compliance.py for detail.")
    return 1 if (strict and total) else 0


if __name__ == "__main__":
    sys.exit(main())
