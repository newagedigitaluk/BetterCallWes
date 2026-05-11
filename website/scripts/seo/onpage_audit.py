"""On-page SEO audit — pulls technical signals for our key pages.

Uses DataForSEO's on_page/instant_pages endpoint (~$0.0011 per page) to fetch
title, meta description, content metrics, internal/external link counts,
broken-link signals, page speed metrics, and content checks for each URL.

Writes raw JSON per page to
~/obsidian-vault/Better-Call-Wes/SEO-Data/onpage/YYYY-MM-DD/<slug>.json
and a roll-up markdown report listing every issue we should fix at
~/obsidian-vault/Better-Call-Wes/SEO-Reports/onpage-YYYY-MM-DD.md.

Usage:
    python3 website/scripts/seo/onpage_audit.py --urls https://bettercallwes.co.uk/
    python3 website/scripts/seo/onpage_audit.py --preset core   # ~9 pages
    python3 website/scripts/seo/onpage_audit.py --preset all    # ~50+ pages
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dataforseo_client import DataForSEOClient, DataForSEOError

ONPAGE_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "onpage"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"
SITE = "https://bettercallwes.co.uk"

CORE_PATHS = [
    "/",
    "/services",
    "/about",
    "/pricing",
    "/reviews",
    "/contact",
    "/booking",
    "/locations",
]

SERVICE_PATHS = [
    "/services/boiler-repair",
    "/services/boiler-servicing",
    "/services/boiler-installation",
    "/services/new-boiler",
    "/services/gas-safety-check",
    "/services/landlord-gas-safety-certificates",
    "/services/emergency-plumber" if False else "/services/plumbing-repairs",
    "/services/pipe-leak-repair",
    "/services/central-heating",
    "/services/power-flushing",
    "/services/radiators",
    "/services/showers",
    "/services/taps",
]

LOCATION_PATHS = [
    f"/locations/{slug}"
    for slug in [
        "bassett",
        "bitterne",
        "bitterne-park",
        "bitterne-village",
        "chandlers-ford",
        "eastleigh",
        "freemantle",
        "harefield",
        "hedge-end",
        "highfield",
        "lordshill",
        "maybush",
        "millbrook",
        "portswood",
        "shirley",
        "southampton",
        "st-denys",
        "swaythling",
    ]
]


def slug_for(url: str) -> str:
    s = url.replace("https://", "").replace("http://", "")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "root"


def preset_urls(preset: str) -> list[str]:
    if preset == "core":
        return [SITE + p for p in CORE_PATHS]
    if preset == "services":
        return [SITE + p for p in SERVICE_PATHS]
    if preset == "locations":
        return [SITE + p for p in LOCATION_PATHS]
    if preset == "all":
        return [SITE + p for p in CORE_PATHS + SERVICE_PATHS + LOCATION_PATHS]
    raise ValueError(f"Unknown preset: {preset}")


def fetch_page(client: DataForSEOClient, url: str) -> dict[str, Any]:
    payload = [
        {
            "url": url,
            "enable_javascript": False,
            "load_resources": False,
            "enable_browser_rendering": False,
        }
    ]
    return client.post("/v3/on_page/instant_pages", payload)


def parse_page(raw: dict[str, Any], url: str) -> dict[str, Any]:
    if not raw.get("tasks"):
        return {"url": url, "error": "no tasks"}
    task = raw["tasks"][0]
    if task.get("status_code") != 20000:
        return {"url": url, "error": task.get("status_message"), "raw_status": task.get("status_code")}
    results = task.get("result") or []
    if not results:
        return {"url": url, "error": "empty result"}
    res = results[0]
    items = res.get("items") or []
    if not items:
        return {"url": url, "error": "no items"}
    page = items[0]

    meta = page.get("meta") or {}
    onpage = page.get("onpage_score")
    content = meta.get("content") or {}
    htags = meta.get("htags") or {}
    checks = page.get("checks") or {}

    issues = sorted(
        [k for k, v in checks.items() if v is True and k in BAD_WHEN_TRUE]
        + [k for k, v in checks.items() if v is False and k in GOOD_WHEN_TRUE]
    )

    return {
        "url": url,
        "status_code": page.get("status_code"),
        "fetch_time": page.get("fetch_time"),
        "size": page.get("size"),
        "encoded_size": page.get("encoded_size"),
        "duration_time": page.get("total_transfer_time"),
        "onpage_score": onpage,
        "title": meta.get("title"),
        "title_length": meta.get("title_length") or (len(meta["title"]) if meta.get("title") else None),
        "description": meta.get("description"),
        "description_length": meta.get("description_length")
        or (len(meta["description"]) if meta.get("description") else None),
        "canonical": meta.get("canonical"),
        "h1": htags.get("h1"),
        "h2_count": len(htags.get("h2") or []),
        "h3_count": len(htags.get("h3") or []),
        "internal_links": meta.get("internal_links_count"),
        "external_links": meta.get("external_links_count"),
        "images_count": meta.get("images_count"),
        "images_without_alt": meta.get("images_size_count")
        and meta.get("images_count_with_alt") is None
        or None,
        "plaintext_word_count": content.get("plain_text_word_count"),
        "plaintext_size": content.get("plain_text_size"),
        "automated_readability_index": content.get("automated_readability_index"),
        "issues_present": issues,
        "raw_checks": checks,
    }


BAD_WHEN_TRUE = {
    "no_title",
    "title_too_long",
    "title_too_short",
    "no_description",
    "duplicate_meta_tags",
    "duplicate_title_tag",
    "duplicate_description_tag",
    "no_h1_tag",
    "no_image_alt",
    "no_favicon",
    "no_doctype",
    "no_encoding_meta_tag",
    "no_content_encoding",
    "high_loading_time",
    "high_waiting_time",
    "is_4xx_code",
    "is_5xx_code",
    "is_broken",
    "is_http",
    "low_content_rate",
    "low_readability_rate",
    "small_page_size",
    "large_page_size",
    "irrelevant_description",
    "irrelevant_meta_keywords",
    "irrelevant_title",
    "deprecated_html_tags",
    "frame",
    "lorem_ipsum",
    "has_render_blocking_resources",
    "has_meta_refresh_redirect",
    "broken_resources",
    "broken_links",
    "size_greater_than_3mb",
}

GOOD_WHEN_TRUE = {
    "canonical",
    "is_https",
    "seo_friendly_url",
    "seo_friendly_url_characters_check",
    "seo_friendly_url_dynamic_check",
    "seo_friendly_url_keywords_check",
    "seo_friendly_url_relative_length_check",
    "has_html_doctype",
}


def build_report(date_str: str, pages: list[dict[str, Any]], total_cost: float) -> str:
    ok = [p for p in pages if "error" not in p]
    errored = [p for p in pages if "error" in p]
    avg_onpage = (
        sum(p.get("onpage_score") or 0 for p in ok) / len(ok) if ok else 0
    )

    lines = [
        f"# On-page audit — {date_str}",
        "",
        f"- Pages audited: **{len(pages)}** "
        f"  •  Errors: **{len(errored)}**"
        f"  •  Average on-page score: **{avg_onpage:.1f}/100**",
        f"- API cost: **${total_cost:.4f}**",
        "",
        "## Page scores",
        "",
        "| URL | Score | Status | Title length | Description length | Words | H1 | Issues |",
        "|---|---:|---|---:|---:|---:|---|---|",
    ]
    for p in sorted(ok, key=lambda x: x.get("onpage_score") or 0):
        issues = ", ".join(p["issues_present"]) or "—"
        h1 = (p.get("h1") or [None])[0] if isinstance(p.get("h1"), list) else p.get("h1") or "—"
        lines.append(
            f"| {p['url']} "
            f"| {p.get('onpage_score') or '—'} "
            f"| {p.get('status_code') or '—'} "
            f"| {p.get('title_length') or '—'} "
            f"| {p.get('description_length') or '—'} "
            f"| {p.get('plaintext_word_count') or '—'} "
            f"| {h1 or '—'} "
            f"| {issues} |"
        )

    if errored:
        lines.append("")
        lines.append("## Errored pages")
        lines.append("")
        for p in errored:
            lines.append(f"- {p['url']} — {p.get('error')}")

    lines.append("")
    lines.append("## Common issues across the site")
    lines.append("")
    issue_counts: dict[str, int] = {}
    for p in ok:
        for i in p.get("issues_present") or []:
            issue_counts[i] = issue_counts.get(i, 0) + 1
    if issue_counts:
        lines.append("| Issue | Page count |")
        lines.append("|---|---:|")
        for name, n in sorted(issue_counts.items(), key=lambda kv: -kv[1]):
            lines.append(f"| {name} | {n} |")
    else:
        lines.append("_No negative checks raised._")
    lines.append("")
    lines.append("## Suggested fixes")
    lines.append("")
    lines.append("- Titles outside 30–60 chars: rewrite to ~55 chars, lead with primary keyword.")
    lines.append("- Descriptions outside 70–160 chars: rewrite to ~155 chars with a clear value prop and a soft CTA.")
    lines.append("- Pages with `no_h1_tag` or duplicate H1: add a single, keyword-led H1.")
    lines.append("- Pages with `low_content_rate`: aim for 500+ words of genuinely useful local content (not filler).")
    lines.append("- Pages with `no_image_alt`: add descriptive alt text — also benefits screen readers.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--urls", help="comma-separated absolute URLs")
    parser.add_argument(
        "--preset",
        choices=("core", "services", "locations", "all"),
        help="preset URL set",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the URL list and exit without spending credits",
    )
    args = parser.parse_args()

    if args.urls:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]
    elif args.preset:
        urls = preset_urls(args.preset)
    else:
        urls = [SITE + "/"]

    if args.dry_run:
        print(f"urls: {len(urls)}")
        for u in urls:
            print(f"  - {u}")
        print(f"\nestimated cost: ${len(urls) * 0.0011:.4f}")
        return 0

    today = date.today().isoformat()
    out_dir = ONPAGE_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)

    client = DataForSEOClient()
    parsed: list[dict[str, Any]] = []
    total_cost = 0.0
    for url in urls:
        print(f"[onpage] fetching: {url}")
        try:
            raw = fetch_page(client, url)
        except DataForSEOError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            parsed.append({"url": url, "error": str(e)})
            continue
        cost = float(raw.get("cost") or 0)
        total_cost += cost
        info = parse_page(raw, url)
        info["cost_usd"] = cost
        parsed.append(info)
        slug = slug_for(url)
        (out_dir / f"{slug}.json").write_text(
            json.dumps({"raw": raw, "parsed": info}, indent=2), encoding="utf-8"
        )
        if "error" in info:
            print(f"  ERROR: {info['error']}")
        else:
            print(
                f"  score: {info.get('onpage_score')}  "
                f"title: {info.get('title_length')} chars  "
                f"desc: {info.get('description_length')} chars  "
                f"issues: {len(info.get('issues_present') or [])}  "
                f"cost: ${cost:.4f}"
            )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORT_DIR / f"onpage-{today}.md"
    out_md.write_text(build_report(today, parsed, total_cost), encoding="utf-8")
    print(f"\n[onpage] report: {out_md}")
    print(f"[onpage] total cost: ${total_cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
