"""Backlink profile audit — us vs top competitors. (VebAPI primary.)

Pulls summary metrics + referring-domain lists from VebAPI for us and every
competitor in the default set, then highlights:
  - Multi-competitor referring domains we are NOT on yet → outreach targets.
  - Known UK citation domains found in competitor profiles → quick wins.

Output:
    SEO-Data/backlinks/YYYY-MM-DD/<domain>.json
    SEO-Reports/backlinks-YYYY-MM-DD.md

Why VebAPI: 31% overlap with DataForSEO in our 2026-05-11 comparison shows
each index has unique blind spots, but VebAPI Scout ($9/mo) gives us
comparable signal volume at <10% of the $100/mo DataForSEO Backlinks
commitment. See `backlinks_compare.py` and `backlinks_dfs.py` for the DFS
alternative when forensic completeness is needed.

Usage:
    python3 website/scripts/seo/backlinks.py
    python3 website/scripts/seo/backlinks.py --competitors brennanheating.co.uk,csheating-ltd.com
    python3 website/scripts/seo/backlinks.py --rows 500
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from competitor_intel import DEFAULT_COMPETITORS, OUR_DOMAIN
from vebapi_client import VebAPIClient, VebAPIError

DATA_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "backlinks"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"

SPAM_TLDS = {
    ".top", ".cfd", ".sbs", ".monster", ".homes", ".cloud", ".store",
    ".wiki", ".biz", ".store", ".bz", ".cn", ".website", ".online",
}


def _is_likely_spam(domain: str, rank: int | None) -> bool:
    if rank is not None and rank >= 70:
        return False
    for tld in SPAM_TLDS:
        if domain.endswith(tld):
            return True
    return False


CITATION_DOMAINS = {
    "checkatrade.com",
    "trustatrader.com",
    "ratedpeople.com",
    "mybuilder.com",
    "yell.com",
    "yelp.co.uk",
    "yelp.com",
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
    "fyple.co.uk",
    "approvedbusiness.co.uk",
    "businessfinder.uk",
    "where2go.com",
}


def _normalise(d: str | None) -> str:
    d = (d or "").strip().lower()
    if not d:
        return ""
    if d.startswith("http://") or d.startswith("https://"):
        d = d.split("://", 1)[1]
    if d.startswith("www."):
        d = d[4:]
    return d.split("/", 1)[0]


def fetch_summary(client: VebAPIClient, domain: str) -> dict[str, Any]:
    raw = client.get("/api/seo/backlinkdata", {"website": domain})
    counts = raw.get("counts") or {}
    bl = counts.get("backlinks") or {}
    dom = counts.get("domains") or {}
    return {
        "backlinks": bl.get("total"),
        "dofollow_backlinks": bl.get("doFollow"),
        "backlinks_from_homepage": bl.get("fromHomePage"),
        "referring_domains": dom.get("total"),
        "dofollow_referring_domains": dom.get("doFollow"),
        "top_backlinks": [
            {
                "url_from": item.get("url_from"),
                "url_to": item.get("url_to"),
                "anchor": item.get("anchor"),
                "nofollow": item.get("nofollow"),
                "domain_rank": item.get("domain_inlink_rank"),
                "first_seen": item.get("first_seen"),
            }
            for item in (raw.get("backlinks") or [])[:25]
        ],
    }


def fetch_refdomains(
    client: VebAPIClient, domain: str, rows: int
) -> list[dict[str, Any]]:
    raw = client.get(
        "/api/seo/referraldomains", {"website": domain, "rows": rows}
    )
    out: list[dict[str, Any]] = []
    for entry in raw.get("referrers") or []:
        out.append(
            {
                "domain": _normalise(entry.get("refdomain")),
                "backlinks": entry.get("backlinks"),
                "dofollow_backlinks": entry.get("dofollow_backlinks"),
                "rank": entry.get("domain_inlink_rank"),
                "first_seen": entry.get("first_seen"),
            }
        )
    return [r for r in out if r["domain"]]


def build_report(
    date_str: str,
    summaries: dict[str, dict[str, Any]],
    refdomains: dict[str, list[dict[str, Any]]],
    total_credits: int,
) -> str:
    lines = [
        f"# Backlink profile — {date_str}",
        "",
        f"- Targets analysed: **{len(summaries)}**",
        f"- VebAPI credits used: **{total_credits}**",
        "",
        "## Scoreboard",
        "",
        "| Domain | Backlinks | Dofollow | Referring domains | Dofollow domains |",
        "|---|---:|---:|---:|---:|",
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
            f"| {s.get('dofollow_backlinks') or 0} "
            f"| {s.get('referring_domains') or 0} "
            f"| {s.get('dofollow_referring_domains') or 0} |"
        )
    lines.append("")

    our_refs = {r["domain"] for r in refdomains.get(OUR_DOMAIN, [])}
    competitor_refs: dict[str, list[tuple[str, int, int]]] = {}
    for dom, rows in refdomains.items():
        if dom == OUR_DOMAIN:
            continue
        for r in rows:
            d = r["domain"]
            if not d or d in our_refs:
                continue
            competitor_refs.setdefault(d, []).append(
                (dom, r.get("backlinks") or 0, r.get("rank") or 0)
            )

    lines.append("## Link gap — outreach targets")
    lines.append("")
    lines.append(
        "_Referring domains pointing at **≥2 competitors but not us**, sorted by competitor "
        "count then aggregate backlinks. Highest-priority outreach list._"
    )
    lines.append("")
    gap_all = [
        {
            "domain": d,
            "n_competitors": len(linked),
            "competitors": linked,
            "total_backlinks": sum(b for _, b, _ in linked),
            "best_rank": max((r for _, _, r in linked), default=0),
        }
        for d, linked in competitor_refs.items()
        if len(linked) >= 2
    ]
    gap = [g for g in gap_all if not _is_likely_spam(g["domain"], g["best_rank"])]
    gap.sort(key=lambda x: (-x["n_competitors"], -x["best_rank"], -x["total_backlinks"]))
    spam_filtered = len(gap_all) - len(gap)
    if spam_filtered:
        lines.append(
            f"_Filtered out {spam_filtered} likely-spam domains (low-rank .top/.cfd/.monster/etc. TLDs)._\n"
        )
    if gap:
        lines.append("| Referring domain | Rank | Links to (competitor + backlinks) |")
        lines.append("|---|---:|---|")
        for g in gap[:40]:
            rivals = sorted(g["competitors"], key=lambda x: -x[1])
            rivals_str = ", ".join(f"{d} ({b})" for d, b, _ in rivals)
            lines.append(f"| {g['domain']} | {g['best_rank']} | {rivals_str} |")
    else:
        lines.append("_No multi-competitor link gaps found._")
    lines.append("")

    lines.append("## Easy wins — known UK citation/directory domains")
    lines.append("")
    lines.append(
        "_Standard UK trade-citation domains seen in competitor backlink profiles. "
        "Get a listing on each — these are mostly free or low-cost and produce immediate "
        "authority signals._"
    )
    lines.append("")
    citation_hits: dict[str, list[str]] = {}
    for r_dom, linked in competitor_refs.items():
        for c in CITATION_DOMAINS:
            if c in r_dom:
                citation_hits.setdefault(c, []).extend(d for d, _, _ in linked)
    our_citation_hits = {c for c in CITATION_DOMAINS for d in our_refs if c in d}
    if citation_hits:
        lines.append("| Citation domain | Used by competitors | We are listed |")
        lines.append("|---|---|---|")
        for c in sorted(citation_hits):
            users = ", ".join(sorted(set(citation_hits[c]))[:5])
            present = "✓" if c in our_citation_hits else "✗"
            lines.append(f"| {c} | {users} | {present} |")
    else:
        lines.append("_No known citation domains in competitor profiles._")
    lines.append("")

    lines.append("## Our top backlinks")
    lines.append("")
    our_summary = summaries.get(OUR_DOMAIN, {})
    top = our_summary.get("top_backlinks") or []
    if top:
        lines.append("| Source | Anchor | Rank | Nofollow |")
        lines.append("|---|---|---:|---|")
        for b in top[:15]:
            anchor = (b.get("anchor") or "")[:40]
            url_from = (b.get("url_from") or "")[:80]
            nf = "yes" if b.get("nofollow") else ""
            lines.append(
                f"| {url_from} | {anchor} | {b.get('domain_rank') or 0} | {nf} |"
            )
    else:
        lines.append("_No backlink samples returned._")
    lines.append("")

    lines.append("## Action plan")
    lines.append("")
    missing_citations = sorted(set(CITATION_DOMAINS) - our_citation_hits)
    citation_to_chase = [c for c in missing_citations if c in citation_hits]
    if citation_to_chase:
        lines.append(
            f"1. List on the {len(citation_to_chase)} citation domains "
            "competitors are using and we're not: "
            + ", ".join(citation_to_chase[:8])
            + "."
        )
    lines.append(
        f"{2 if citation_to_chase else 1}. Outreach to the top "
        f"{min(10, len(gap))} multi-competitor link sources above. "
        "For each, look at the page where the competitor link sits and pitch a comparable contribution "
        "(guest answer for a local blog, supplier directory entry, expert quote for press)."
    )
    lines.append(
        f"{3 if citation_to_chase else 2}. Run this report monthly. Track which outreach attempts "
        "land by watching the **us** row's referring-domain count climb."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitors", help="comma-separated domain list")
    parser.add_argument(
        "--rows",
        type=int,
        default=200,
        help="referring-domain rows to fetch per target (1 credit per 100)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.competitors:
        competitors = [_normalise(c) for c in args.competitors.split(",") if c.strip()]
    else:
        competitors = list(DEFAULT_COMPETITORS)
    targets = [OUR_DOMAIN] + [c for c in competitors if c != OUR_DOMAIN]

    if args.dry_run:
        per = 1 + max(1, (args.rows + 99) // 100)
        est = len(targets) * per
        print(f"targets ({len(targets)}):")
        for d in targets:
            print(f"  - {d}")
        print(f"\nestimated credits: ~{est} (free tier = 50, Scout = 10,000/mo)")
        return 0

    today = date.today().isoformat()
    out_dir = DATA_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    client = VebAPIClient()

    summaries: dict[str, dict[str, Any]] = {}
    refdomains: dict[str, list[dict[str, Any]]] = {}
    total_credits = 0

    for dom in targets:
        print(f"[bl] {dom}")
        try:
            s = fetch_summary(client, dom)
            total_credits += 1
            summaries[dom] = s
            print(
                f"  summary: {s.get('backlinks')} backlinks, "
                f"{s.get('referring_domains')} ref domains  (1 credit)"
            )
        except VebAPIError as e:
            print(f"  summary ERROR: {e}", file=sys.stderr)
            summaries[dom] = {}
            continue

        try:
            rows = fetch_refdomains(client, dom, args.rows)
            credits = max(1, (args.rows + 99) // 100)
            total_credits += credits
            refdomains[dom] = rows
            print(f"  refdomains: {len(rows)} returned  ({credits} credits)")
        except VebAPIError as e:
            print(f"  refdomains ERROR: {e}", file=sys.stderr)
            refdomains[dom] = []

        (out_dir / f"{dom}.json").write_text(
            json.dumps({"summary": s, "refdomains": refdomains[dom]}, indent=2),
            encoding="utf-8",
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORT_DIR / f"backlinks-{today}.md"
    out_md.write_text(
        build_report(today, summaries, refdomains, total_credits),
        encoding="utf-8",
    )
    print(f"\n[bl] report: {out_md}")
    print(f"[bl] total credits used: {total_credits}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
