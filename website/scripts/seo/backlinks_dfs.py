"""Backlink profile audit — us vs top competitors.

Uses DataForSEO's `/v3/backlinks/summary/live` for an overview (referring
domains, rank, anchors) and `/v3/backlinks/referring_domains/live` for the
actual referring-domain list per competitor. The output highlights domains
that link to multiple competitors but not us — those are the best outreach
targets.

Output:
    SEO-Data/backlinks/YYYY-MM-DD/summary-<domain>.json
    SEO-Data/backlinks/YYYY-MM-DD/refdomains-<domain>.json
    SEO-Reports/backlinks-YYYY-MM-DD.md

Usage:
    python3 website/scripts/seo/backlinks.py
    python3 website/scripts/seo/backlinks.py --competitors brennanheating.co.uk
    python3 website/scripts/seo/backlinks.py --skip-refdomains   # summary only (cheaper)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dataforseo_client import DataForSEOClient, DataForSEOError
from competitor_intel import DEFAULT_COMPETITORS, OUR_DOMAIN

DATA_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "backlinks"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"


def fetch_summary(client: DataForSEOClient, domain: str) -> dict[str, Any]:
    payload = [
        {
            "target": domain,
            "include_subdomains": True,
            "internal_list_limit": 10,
            "backlinks_status_type": "live",
        }
    ]
    return client.post("/v3/backlinks/summary/live", payload)


def fetch_refdomains(
    client: DataForSEOClient, domain: str, limit: int = 200
) -> dict[str, Any]:
    payload = [
        {
            "target": domain,
            "include_subdomains": True,
            "limit": limit,
            "order_by": ["backlinks,desc"],
            "backlinks_status_type": "live",
        }
    ]
    return client.post("/v3/backlinks/referring_domains/live", payload)


def parse_summary(raw: dict[str, Any]) -> tuple[dict[str, Any], float]:
    cost = float(raw.get("cost") or 0)
    if not raw.get("tasks"):
        return {}, cost
    task = raw["tasks"][0]
    if task.get("status_code") != 20000:
        raise DataForSEOError(
            f"backlinks summary failed: {task.get('status_message')}"
        )
    results = task.get("result") or []
    return (results[0] if results else {}), cost


def parse_refdomains(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    cost = float(raw.get("cost") or 0)
    if not raw.get("tasks"):
        return [], cost
    task = raw["tasks"][0]
    if task.get("status_code") != 20000:
        raise DataForSEOError(
            f"referring_domains failed: {task.get('status_message')}"
        )
    rows: list[dict[str, Any]] = []
    for result in task.get("result") or []:
        for item in result.get("items") or []:
            rows.append(
                {
                    "domain": item.get("domain"),
                    "backlinks": item.get("backlinks"),
                    "rank": item.get("rank"),
                    "first_seen": item.get("first_seen"),
                    "is_lost": item.get("is_lost"),
                }
            )
    return rows, cost


def build_report(
    date_str: str,
    summaries: dict[str, dict[str, Any]],
    ref_domain_data: dict[str, list[dict[str, Any]]],
    total_cost: float,
) -> str:
    lines = [
        f"# Backlink profile — {date_str}",
        "",
        f"- Targets analysed: **{len(summaries)}**",
        f"- API cost: **${total_cost:.4f}**",
        "",
        "## Scoreboard",
        "",
        "| Domain | Backlinks | Referring domains | Rank | Lost | Anchor diversity |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    ordered = sorted(
        summaries.items(),
        key=lambda kv: (kv[1].get("referring_domains") or 0),
        reverse=True,
    )
    for dom, s in ordered:
        tag = " **(us)**" if dom == OUR_DOMAIN else ""
        lines.append(
            f"| {dom}{tag} | {s.get('backlinks') or 0} "
            f"| {s.get('referring_domains') or 0} "
            f"| {s.get('rank') or '—'} "
            f"| {s.get('backlinks_lost_count') or 0} "
            f"| {s.get('referring_pages_anchors') or '—'} |"
        )
    lines.append("")

    if ref_domain_data:
        lines.append("## Link gap — domains linking to ≥2 competitors but not us")
        lines.append("")
        our_refs = {
            (r["domain"] or "").lower()
            for r in ref_domain_data.get(OUR_DOMAIN, [])
            if r.get("domain")
        }
        competitor_refs: dict[str, list[tuple[str, int]]] = {}
        for dom, rows in ref_domain_data.items():
            if dom == OUR_DOMAIN:
                continue
            for r in rows:
                d = (r.get("domain") or "").lower()
                if not d or d in our_refs:
                    continue
                competitor_refs.setdefault(d, []).append(
                    (dom, r.get("backlinks") or 0)
                )

        gap = sorted(
            (
                {
                    "domain": d,
                    "competitor_count": len(linked),
                    "competitors": linked,
                    "total_backlinks": sum(b for _, b in linked),
                }
                for d, linked in competitor_refs.items()
                if len(linked) >= 2
            ),
            key=lambda x: (-x["competitor_count"], -x["total_backlinks"]),
        )[:40]

        if gap:
            lines.append("| Referring domain | Links to | Total backlinks across competitors |")
            lines.append("|---|---|---:|")
            for g in gap:
                links_str = ", ".join(
                    f"{d} ({n})" for d, n in sorted(g["competitors"], key=lambda x: -x[1])
                )
                lines.append(
                    f"| {g['domain']} | {links_str} | {g['total_backlinks']} |"
                )
        else:
            lines.append("_No multi-competitor link gaps found._")
        lines.append("")

        lines.append("## Easy wins — directories and citation sites")
        lines.append("")
        lines.append(
            "Known UK trade-citation domains found in competitor profiles. "
            "Get listed on each (free or low-cost in most cases)."
        )
        lines.append("")
        citation_hints = {
            "checkatrade.com",
            "trustatrader.com",
            "ratedpeople.com",
            "mybuilder.com",
            "yell.com",
            "yelp.com",
            "yelp.co.uk",
            "thomsonlocal.com",
            "bark.com",
            "houzz.co.uk",
            "trustpilot.com",
            "google.com",
            "facebook.com",
            "linkedin.com",
            "gassaferegister.co.uk",
            "which.co.uk",
            "watersafe.org.uk",
            "freeindex.co.uk",
            "scoot.co.uk",
            "cylex-uk.co.uk",
            "ratedplaces.com",
            "fyple.co.uk",
        }
        hits: dict[str, list[str]] = {}
        for d in competitor_refs:
            d_l = d.lower()
            for c in citation_hints:
                if c in d_l:
                    hits.setdefault(c, []).append(d)
        if hits:
            for c, found in sorted(hits.items()):
                lines.append(f"- **{c}** — seen in profiles via: {', '.join(sorted(set(found))[:5])}")
        else:
            lines.append("_No known citation domains found in competitor profiles._")
        lines.append("")

    lines.append("## Action plan")
    lines.append("")
    lines.append(
        "1. Submit to every citation domain in the easy-wins list (Trustpilot, Checkatrade, Yell, etc.) within a week."
    )
    lines.append(
        "2. Email outreach to the top 10 multi-competitor link sources — local blogs, news sites, professional directories. "
        "Offer a real value prop (e.g. an expert quote, a deal for their readers)."
    )
    lines.append(
        "3. Audit competitor anchor text on the top referring domains — many will accept similar links to us if asked."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitors", help="comma-separated domain list")
    parser.add_argument(
        "--skip-refdomains",
        action="store_true",
        help="skip the per-domain referring_domains call (summary only — cheaper)",
    )
    parser.add_argument("--limit", type=int, default=200, help="referring domains per target")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.competitors:
        competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]
    else:
        competitors = list(DEFAULT_COMPETITORS)
    targets = [OUR_DOMAIN] + competitors

    if args.dry_run:
        n = len(targets)
        est_summary = n * 0.02
        est_refdomains = 0 if args.skip_refdomains else n * 0.02
        print(f"targets ({n}):")
        for d in targets:
            print(f"  - {d}")
        print(f"\nestimated cost: ~${est_summary + est_refdomains:.4f}")
        return 0

    today = date.today().isoformat()
    out_dir = DATA_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    client = DataForSEOClient()

    summaries: dict[str, dict[str, Any]] = {}
    ref_domain_data: dict[str, list[dict[str, Any]]] = {}
    total_cost = 0.0

    for dom in targets:
        print(f"[bl] summary: {dom}")
        try:
            raw = fetch_summary(client, dom)
            s, cost = parse_summary(raw)
        except DataForSEOError as e:
            msg = str(e)
            print(f"  ERROR: {msg}", file=sys.stderr)
            if "Access denied" in msg or "subscription" in msg.lower():
                print(
                    "\n[bl] DataForSEO Backlinks API subscription is not active.\n"
                    "      Enable at https://app.dataforseo.com/backlinks-subscription "
                    "and re-run.",
                    file=sys.stderr,
                )
                return 2
            continue
        summaries[dom] = s
        total_cost += cost
        (out_dir / f"summary-{dom}.json").write_text(
            json.dumps({"domain": dom, "summary": s, "cost_usd": cost}, indent=2),
            encoding="utf-8",
        )
        print(
            f"  backlinks: {s.get('backlinks')}  ref domains: {s.get('referring_domains')}  cost: ${cost:.4f}"
        )

        if args.skip_refdomains:
            continue

        try:
            raw_rd = fetch_refdomains(client, dom, args.limit)
            rd_rows, rd_cost = parse_refdomains(raw_rd)
        except DataForSEOError as e:
            print(f"  refdomains ERROR: {e}", file=sys.stderr)
            continue
        ref_domain_data[dom] = rd_rows
        total_cost += rd_cost
        (out_dir / f"refdomains-{dom}.json").write_text(
            json.dumps({"domain": dom, "rows": rd_rows, "cost_usd": rd_cost}, indent=2),
            encoding="utf-8",
        )
        print(f"  refdomains: {len(rd_rows)}  cost: ${rd_cost:.4f}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORT_DIR / f"backlinks-{today}.md"
    out_md.write_text(
        build_report(today, summaries, ref_domain_data, total_cost),
        encoding="utf-8",
    )
    print(f"\n[bl] report: {out_md}")
    print(f"[bl] total cost: ${total_cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
