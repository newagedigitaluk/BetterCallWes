"""Pull UK search volumes, CPC and competition for a list of keywords.

Uses DataForSEO's keywords_data/google_ads/search_volume/live endpoint
(bulk: one call handles up to 1,000 keywords for ~$0.05 total). Output is
stored as JSON in ~/obsidian-vault/Better-Call-Wes/SEO-Data/volumes/YYYY-MM-DD.json
and a markdown summary at .../SEO-Reports/volumes-YYYY-MM-DD.md.

Usage:
    python3 website/scripts/seo/keyword_volumes.py            # tier_1_weekly
    python3 website/scripts/seo/keyword_volumes.py --tier tier_3_quarterly_long_tail
    python3 website/scripts/seo/keyword_volumes.py --keywords "boiler repair Bitterne,plumber Southampton"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dataforseo_client import DataForSEOClient, DataForSEOError
from serp_tracker import CONFIG_PATH

UK_LOCATION_CODE = 2826
LANGUAGE_CODE = "en"

VOLUMES_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "volumes"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"


def load_tier(tier: str) -> list[str]:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if tier in cfg and isinstance(cfg[tier], list):
        return list(cfg[tier])
    if tier == "tier_2_monthly":
        services = cfg["tier_2_monthly_services"]
        locations = cfg["tier_2_monthly_locations"]
        return [f"{s} {loc.replace('-', ' ')}" for s in services for loc in locations]
    raise ValueError(f"Unknown tier: {tier}")


def fetch_volumes(client: DataForSEOClient, keywords: list[str]) -> dict[str, Any]:
    payload = [
        {
            "keywords": keywords,
            "location_code": UK_LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
        }
    ]
    return client.post(
        "/v3/keywords_data/google_ads/search_volume/live", payload
    )


def parse_volumes(raw: dict[str, Any]) -> list[dict[str, Any]]:
    if not raw.get("tasks"):
        return []
    task = raw["tasks"][0]
    if task.get("status_code") != 20000:
        raise DataForSEOError(
            f"Volumes task failed: {task.get('status_message')}"
        )
    out: list[dict[str, Any]] = []
    for r in task.get("result") or []:
        out.append(
            {
                "keyword": r.get("keyword"),
                "search_volume": r.get("search_volume"),
                "competition": r.get("competition"),
                "competition_index": r.get("competition_index"),
                "low_top_of_page_bid": r.get("low_top_of_page_bid"),
                "high_top_of_page_bid": r.get("high_top_of_page_bid"),
                "cpc": r.get("cpc"),
            }
        )
    return out


def _fmt_num(v: Any, decimals: int = 2) -> str:
    if isinstance(v, (int, float)):
        return f"{v:.{decimals}f}"
    return "—"


def build_report(date_str: str, rows: list[dict[str, Any]], cost: float, tier: str) -> str:
    rows_sorted = sorted(
        rows, key=lambda r: (r.get("search_volume") or 0), reverse=True
    )
    total_volume = sum(r.get("search_volume") or 0 for r in rows)
    with_volume = sum(1 for r in rows if r.get("search_volume"))

    lines = [
        f"# Keyword volumes — {date_str}",
        "",
        f"- Tier: **{tier}**  •  Keywords: **{len(rows)}**  •  With reported volume: **{with_volume}**",
        f"- Total monthly searches across set: **{total_volume:,}**",
        f"- API cost: **${cost:.4f}**",
        "",
        "## Ranked by monthly search volume",
        "",
        "| Keyword | Vol/mo | Competition | CPC (£) | Low bid | High bid |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for r in rows_sorted:
        vol = r.get("search_volume")
        comp = r.get("competition") or "—"
        lines.append(
            f"| {r['keyword']} | {vol if vol is not None else '—'} | {comp} "
            f"| {_fmt_num(r.get('cpc'))} | {_fmt_num(r.get('low_top_of_page_bid'))} "
            f"| {_fmt_num(r.get('high_top_of_page_bid'))} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- Volumes are Google Ads broad-match estimates for the UK and rounded into buckets. "
        "Use them for relative prioritisation, not absolute traffic forecasting."
    )
    lines.append(
        "- A keyword with 'low' competition but reported CPC > £5 is usually a high-intent commercial term — worth a dedicated landing page."
    )
    lines.append(
        "- Zero or null volume often means the term is too long-tail to be measured individually; it may still aggregate to real traffic."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="tier_1_weekly")
    parser.add_argument(
        "--keywords",
        help="comma-separated keyword list (overrides --tier)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the keyword list and exit without spending credits",
    )
    args = parser.parse_args()

    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = load_tier(args.tier)

    if args.dry_run:
        print(f"tier: {args.tier}  count: {len(keywords)}")
        for k in keywords:
            print(f"  - {k}")
        print("\nestimated cost: ~$0.05 (bulk endpoint, flat per call)")
        return 0

    today = date.today().isoformat()
    client = DataForSEOClient()
    print(f"[vol] fetching volumes for {len(keywords)} keyword(s)…")
    raw = fetch_volumes(client, keywords)
    cost = float(raw.get("cost") or 0)
    rows = parse_volumes(raw)

    tier_slug = args.tier if not args.keywords else "custom"
    VOLUMES_DIR.mkdir(parents=True, exist_ok=True)
    out_json = VOLUMES_DIR / f"{today}-{tier_slug}.json"
    out_json.write_text(
        json.dumps(
            {
                "captured_at": today,
                "tier": tier_slug,
                "cost_usd": cost,
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORT_DIR / f"volumes-{today}-{tier_slug}.md"
    out_md.write_text(build_report(today, rows, cost, tier_slug), encoding="utf-8")

    print(f"[vol] data: {out_json}")
    print(f"[vol] report: {out_md}")
    print(f"[vol] cost: ${cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
