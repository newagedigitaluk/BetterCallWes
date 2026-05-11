"""Competitor keyword intelligence — what they rank for, what we don't.

Uses DataForSEO Labs `dataforseo_labs/google/ranked_keywords/live` to pull every
keyword a competitor domain ranks for on Google UK. Compares against our own
ranked keywords to surface gaps — keywords they rank for in the top 20 that we
don't appear for.

Output:
    SEO-Data/competitors/YYYY-MM-DD/<domain>.json
    SEO-Reports/competitor-intel-YYYY-MM-DD.md

Usage:
    python3 website/scripts/seo/competitor_intel.py
    python3 website/scripts/seo/competitor_intel.py --competitors brennanheating.co.uk,gassedupheating.co.uk
    python3 website/scripts/seo/competitor_intel.py --limit 200
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dataforseo_client import DataForSEOClient, DataForSEOError

UK_LOCATION_CODE = 2826
LANGUAGE_CODE = "en"
OUR_DOMAIN = "bettercallwes.co.uk"

DEFAULT_COMPETITORS = [
    "brennanheating.co.uk",
    "gassedupheating.co.uk",
    "southplumbing.co.uk",
    "ukbplumbing.co.uk",
    "gas-bright.co.uk",
    "heattechhampshire.com",
    "prospectheatsolutions.co.uk",
    "csheating-ltd.com",
    "aerenewables.co.uk",
    "geharding.co.uk",
]

DATA_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "competitors"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"


def fetch_ranked(client: DataForSEOClient, domain: str, limit: int) -> dict[str, Any]:
    payload = [
        {
            "target": domain,
            "location_code": UK_LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
            "limit": limit,
            "filters": [["ranked_serp_element.serp_item.rank_absolute", "<=", 20]],
            "order_by": ["keyword_data.keyword_info.search_volume,desc"],
        }
    ]
    return client.post(
        "/v3/dataforseo_labs/google/ranked_keywords/live", payload
    )


def parse_ranked(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    cost = float(raw.get("cost") or 0)
    if not raw.get("tasks"):
        return [], cost
    task = raw["tasks"][0]
    if task.get("status_code") != 20000:
        raise DataForSEOError(
            f"ranked_keywords failed: {task.get('status_message')}"
        )
    items: list[dict[str, Any]] = []
    for result in task.get("result") or []:
        for entry in result.get("items") or []:
            kw_info = (entry.get("keyword_data") or {}).get("keyword_info") or {}
            serp_item = (entry.get("ranked_serp_element") or {}).get("serp_item") or {}
            items.append(
                {
                    "keyword": (entry.get("keyword_data") or {}).get("keyword"),
                    "rank": serp_item.get("rank_absolute"),
                    "url": serp_item.get("url"),
                    "title": serp_item.get("title"),
                    "search_volume": kw_info.get("search_volume"),
                    "cpc": kw_info.get("cpc"),
                    "competition": kw_info.get("competition_level"),
                    "search_intent": (
                        (entry.get("keyword_data") or {}).get("search_intent_info") or {}
                    ).get("main_intent"),
                }
            )
    return items, cost


def build_report(
    date_str: str,
    our_keywords: list[dict[str, Any]],
    competitor_data: dict[str, list[dict[str, Any]]],
    total_cost: float,
) -> str:
    our_kw_set = {(r["keyword"] or "").lower() for r in our_keywords if r.get("keyword")}

    lines = [
        f"# Competitor intel — {date_str}",
        "",
        f"- Our keywords in top 20: **{len(our_keywords)}**",
        f"- Competitors analysed: **{len(competitor_data)}**",
        f"- API cost: **${total_cost:.4f}**",
        "",
    ]

    lines.append("## Our top ranked keywords")
    lines.append("")
    if our_keywords:
        lines.append("| Keyword | Our rank | Vol/mo | CPC | Intent |")
        lines.append("|---|---:|---:|---:|---|")
        for r in sorted(
            our_keywords,
            key=lambda x: (-(x.get("search_volume") or 0), x.get("rank") or 99),
        )[:25]:
            lines.append(
                f"| {r['keyword']} | #{r['rank']} | {r.get('search_volume') or '—'} "
                f"| {_money(r.get('cpc'))} | {r.get('search_intent') or '—'} |"
            )
    else:
        lines.append("_No keywords ranking in top 20._")
    lines.append("")

    lines.append("## Competitor scoreboard")
    lines.append("")
    lines.append("| Competitor | Keywords in top 20 | Top-3 share | Avg position |")
    lines.append("|---|---:|---:|---:|")
    for dom, rows in sorted(
        competitor_data.items(), key=lambda kv: -len(kv[1])
    ):
        top3 = sum(1 for r in rows if (r.get("rank") or 99) <= 3)
        avg_pos = (
            sum(r.get("rank") or 0 for r in rows) / len(rows) if rows else 0
        )
        lines.append(
            f"| {dom} | {len(rows)} | {top3} | {avg_pos:.1f} |"
        )
    lines.append("")

    lines.append("## Top content gaps (they rank, we don't)")
    lines.append("")
    lines.append(
        "_Keywords where ≥1 competitor ranks in top 20 but we don't appear._"
    )
    lines.append("")

    gap_map: dict[str, dict[str, Any]] = {}
    for dom, rows in competitor_data.items():
        for r in rows:
            kw = (r.get("keyword") or "").lower()
            if not kw or kw in our_kw_set:
                continue
            if kw not in gap_map:
                gap_map[kw] = {
                    "keyword": r["keyword"],
                    "search_volume": r.get("search_volume") or 0,
                    "cpc": r.get("cpc"),
                    "intent": r.get("search_intent"),
                    "competitors": [],
                }
            gap_map[kw]["competitors"].append((dom, r.get("rank")))

    gaps = sorted(
        gap_map.values(),
        key=lambda x: (-(x["search_volume"] or 0), -len(x["competitors"])),
    )[:50]

    if gaps:
        lines.append("| Keyword | Vol/mo | CPC | Intent | Competitors ranking |")
        lines.append("|---|---:|---:|---|---|")
        for g in gaps:
            competitors_str = ", ".join(
                f"{d} #{r}" for d, r in sorted(g["competitors"], key=lambda x: x[1] or 99)[:3]
            )
            lines.append(
                f"| {g['keyword']} | {g['search_volume'] or '—'} | {_money(g['cpc'])} "
                f"| {g['intent'] or '—'} | {competitors_str} |"
            )
    else:
        lines.append("_No gaps found (or competitors returned no data)._")
    lines.append("")

    lines.append("## How to use this")
    lines.append("")
    lines.append(
        "- Top-of-table content gaps with high volume + commercial intent = highest priority "
        "for new pages or expansion of existing ones."
    )
    lines.append(
        "- Repeat competitor-rank-appearances (3+) signal the topic is a known winner in this niche."
    )
    lines.append(
        "- Check which exact URL a competitor ranks with — often a service-specific or location page "
        "we should mirror with our own angle."
    )
    return "\n".join(lines)


def _money(v: Any) -> str:
    if isinstance(v, (int, float)):
        return f"£{v:.2f}"
    return "—"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--competitors",
        help="comma-separated domain list (overrides default)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="max keywords per competitor (default 200)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.competitors:
        competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]
    else:
        competitors = list(DEFAULT_COMPETITORS)

    targets = [OUR_DOMAIN] + competitors

    if args.dry_run:
        print(f"targets ({len(targets)}):")
        for d in targets:
            print(f"  - {d}")
        est = len(targets) * 0.01
        print(f"\nestimated cost: ~${est:.4f} ($0.01 per ranked_keywords call)")
        return 0

    today = date.today().isoformat()
    out_dir = DATA_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    client = DataForSEOClient()

    our_rows: list[dict[str, Any]] = []
    competitor_data: dict[str, list[dict[str, Any]]] = {}
    total_cost = 0.0

    for dom in targets:
        print(f"[comp] fetching: {dom}")
        try:
            raw = fetch_ranked(client, dom, args.limit)
        except DataForSEOError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue
        rows, cost = parse_ranked(raw)
        total_cost += cost
        (out_dir / f"{dom.replace('/', '_')}.json").write_text(
            json.dumps({"domain": dom, "rows": rows, "cost_usd": cost}, indent=2),
            encoding="utf-8",
        )
        if dom == OUR_DOMAIN:
            our_rows = rows
        else:
            competitor_data[dom] = rows
        print(f"  {len(rows)} keywords  cost: ${cost:.4f}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORT_DIR / f"competitor-intel-{today}.md"
    out_md.write_text(
        build_report(today, our_rows, competitor_data, total_cost),
        encoding="utf-8",
    )
    print(f"\n[comp] report: {out_md}")
    print(f"[comp] total cost: ${total_cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
