#!/usr/bin/env python3
"""Keep the review figures on the site in step with one source.

The Google rating and the review counts appear in about 90 places. They used to be
typed by hand, which is how the site ended up saying 4.9 and 5.0, 120+ and 200+, all
at once. Now each figure sits in a marked span, e.g.

    <span data-trust="google-count">131</span>

and the Google review links carry data-trust-link="google".

Edit trust_figures.json, then:

    python3 website/scripts/update_trust_figures.py           # rewrite every span
    python3 website/scripts/update_trust_figures.py --check   # report only, exit 1 if stale

--check also flags rating or review claims typed outside the spans, so a new page
can't quietly bring the drift back.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent / "site"
FIGS = json.loads((HERE / "trust_figures.json").read_text(encoding="utf-8"))

VALUES = {
    "google-rating": FIGS["google_rating"],
    "google-count": FIGS["google_count"],
    "total-count": FIGS["total_count"],
    "site-count": FIGS["site_count"],
    "site-count-word": FIGS["site_count_word"],
}
SPAN = re.compile(r'(<span data-trust="([a-z-]+)">)(.*?)(</span>)')
LINK = re.compile(r'(<a data-trust-link="google" href=")([^"]*)(")')

# Phrases that should only ever come out of a span. Meta descriptions and JSON-LD
# can't hold spans, so they keep plain "5.0" / "200+" wording and are listed for a
# manual check instead of flagged.
STRAY = [
    (re.compile(r"\b4\.\d\s*(?:&#9733;|★)?\s*(?:on Google|from|[Aa]verage)"), "a 4.x rating"),
    (re.compile(r"\b\d{2,3}\+?\s+(?:five-star|5-star|Google|[Vv]erified)\s+[Rr]eviews"), "a hand-typed review count"),
    (re.compile(r"Trustpilot"), "Trustpilot, which is not one of the review sites"),
]


def main() -> int:
    check = "--check" in sys.argv
    stale = changed = 0
    problems = []
    for path in sorted(list(SITE.rglob("*.html")) + list(SITE.rglob("*.txt"))):
        text = path.read_text(encoding="utf-8")
        new = text

        def fix_span(m):
            nonlocal stale
            want = VALUES.get(m.group(2))
            if want is None:
                problems.append(f"{path.relative_to(SITE)}: unknown data-trust key '{m.group(2)}'")
                return m.group(0)
            if m.group(3) != want:
                stale += 1
            return m.group(1) + want + m.group(4)

        def fix_link(m):
            nonlocal stale
            if m.group(2) != FIGS["google_url"]:
                stale += 1
            return m.group(1) + FIGS["google_url"] + m.group(3)

        new = SPAN.sub(fix_span, new)
        new = LINK.sub(fix_link, new)

        bare = SPAN.sub("", new)
        for rx, why in STRAY:
            for m in rx.finditer(bare):
                line = bare.count("\n", 0, m.start()) + 1
                problems.append(f"{path.relative_to(SITE)}:{line}: {why}: '{m.group(0)}'")

        if new != text and not check:
            path.write_text(new, encoding="utf-8")
            changed += 1

    if check:
        print(f"{stale} stale figure(s).")
    else:
        print(f"Updated {changed} file(s).")
    for p in problems:
        print("  " + p)
    print("Not updated by this script (meta descriptions, JSON-LD, llms.txt): if the"
          " rating or the 200+ total ever changes, grep the site for the old value.")
    return 1 if (check and (stale or problems)) or problems else 0


if __name__ == "__main__":
    sys.exit(main())
