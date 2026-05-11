"""Side-by-side backlink comparison: DataForSEO vs VebAPI.

For each test domain, pulls the referring-domain list from both providers,
computes overlap and unique counts, and writes a markdown report. Helps
decide whether VebAPI's cheaper subscription is a viable substitute for
DataForSEO's $100/month Backlinks commitment.

Usage:
    python3 website/scripts/seo/backlinks_compare.py
    python3 website/scripts/seo/backlinks_compare.py --domains bettercallwes.co.uk,brennanheating.co.uk --rows 200
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dataforseo_client import DataForSEOClient, DataForSEOError
from vebapi_client import VebAPIClient, VebAPIError

REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"
DATA_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "backlinks-compare"

DEFAULT_DOMAINS = [
    "bettercallwes.co.uk",
    "csheating-ltd.com",
    "brennanheating.co.uk",
    "gassedupheating.co.uk",
    "ukbplumbing.co.uk",
]


def normalise_domain(d: str) -> str:
    d = (d or "").strip().lower()
    if not d:
        return ""
    if d.startswith("http://") or d.startswith("https://"):
        d = d.split("://", 1)[1]
    if d.startswith("www."):
        d = d[4:]
    return d.split("/", 1)[0]


def dfs_summary_and_refdomains(
    client: DataForSEOClient, domain: str, rows: int
) -> tuple[dict[str, Any], list[str], float]:
    cost = 0.0
    summary_payload = [
        {"target": domain, "include_subdomains": True, "backlinks_status_type": "live"}
    ]
    r1 = client.post("/v3/backlinks/summary/live", summary_payload)
    cost += float(r1.get("cost") or 0)
    sresult = (r1.get("tasks") or [{}])[0].get("result") or []
    summary = sresult[0] if sresult else {}

    rd_payload = [
        {
            "target": domain,
            "include_subdomains": True,
            "limit": rows,
            "order_by": ["backlinks,desc"],
            "backlinks_status_type": "live",
        }
    ]
    r2 = client.post("/v3/backlinks/referring_domains/live", rd_payload)
    cost += float(r2.get("cost") or 0)
    rd_items: list[str] = []
    for result in (r2.get("tasks") or [{}])[0].get("result") or []:
        for item in result.get("items") or []:
            d = normalise_domain(item.get("domain") or "")
            if d:
                rd_items.append(d)
    return summary, rd_items, cost


def veb_summary_and_refdomains(
    client: VebAPIClient, domain: str, rows: int
) -> tuple[dict[str, Any], list[str], int]:
    credits = 0
    r1 = client.get("/api/seo/backlinkdata", {"website": domain})
    credits += 1
    counts = r1.get("counts") or {}
    summary = {
        "backlinks": (counts.get("backlinks") or {}).get("total"),
        "referring_domains": (counts.get("domains") or {}).get("total"),
        "dofollow_backlinks": (counts.get("backlinks") or {}).get("doFollow"),
    }

    r2 = client.get(
        "/api/seo/referraldomains", {"website": domain, "rows": rows}
    )
    credits += max(1, (rows + 99) // 100)
    rd_items: list[str] = []
    for entry in r2.get("referrers") or []:
        d = normalise_domain(entry.get("refdomain") or "")
        if d:
            rd_items.append(d)
    return summary, rd_items, credits


def build_report(
    date_str: str,
    results: list[dict[str, Any]],
    dfs_cost: float,
    veb_credits: int,
) -> str:
    lines = [
        f"# Backlinks provider comparison — {date_str}",
        "",
        f"- Domains tested: **{len(results)}**",
        f"- DataForSEO spend: **${dfs_cost:.4f}**",
        f"- VebAPI credits used: **{veb_credits}** (≈${veb_credits * 0.0009:.4f} on Scout tier)",
        "",
        "## Scoreboard",
        "",
        "| Domain | DFS backlinks | Veb backlinks | DFS ref domains | Veb ref domains | Overlap | Veb / DFS coverage |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        dfs_bl = r["dfs_summary"].get("backlinks") or 0
        veb_bl = r["veb_summary"].get("backlinks") or 0
        dfs_rd_set = set(r["dfs_refdomains"])
        veb_rd_set = set(r["veb_refdomains"])
        overlap = len(dfs_rd_set & veb_rd_set)
        coverage_pct = (overlap * 100 / len(dfs_rd_set)) if dfs_rd_set else 0
        lines.append(
            f"| {r['domain']} | {dfs_bl} | {veb_bl} "
            f"| {len(dfs_rd_set)} | {len(veb_rd_set)} | {overlap} | {coverage_pct:.0f}% |"
        )
    lines.append("")

    total_dfs = sum(len(set(r["dfs_refdomains"])) for r in results)
    total_veb = sum(len(set(r["veb_refdomains"])) for r in results)
    total_overlap = sum(
        len(set(r["dfs_refdomains"]) & set(r["veb_refdomains"])) for r in results
    )
    lines.append("## Aggregate")
    lines.append("")
    lines.append(
        f"- Total unique referring domains discovered: DFS **{total_dfs}** • Veb **{total_veb}** • Overlap **{total_overlap}**"
    )
    if total_dfs:
        lines.append(
            f"- VebAPI overall coverage of DFS index: **{total_overlap * 100 / total_dfs:.0f}%**"
        )
    veb_only = sum(
        len(set(r["veb_refdomains"]) - set(r["dfs_refdomains"])) for r in results
    )
    lines.append(
        f"- VebAPI found **{veb_only}** referring domains DFS missed (might be index freshness or different methodology)."
    )
    lines.append("")

    lines.append("## Per-domain detail")
    lines.append("")
    for r in results:
        d = r["domain"]
        dfs_rd_set = set(r["dfs_refdomains"])
        veb_rd_set = set(r["veb_refdomains"])
        only_dfs = dfs_rd_set - veb_rd_set
        only_veb = veb_rd_set - dfs_rd_set
        both = dfs_rd_set & veb_rd_set
        lines.append(f"### {d}")
        lines.append("")
        lines.append(
            f"- DFS summary: **{r['dfs_summary'].get('backlinks')}** backlinks, "
            f"**{r['dfs_summary'].get('referring_domains')}** ref domains "
            f"(DR/rank: {r['dfs_summary'].get('rank')})"
        )
        lines.append(
            f"- Veb summary: **{r['veb_summary'].get('backlinks')}** backlinks, "
            f"**{r['veb_summary'].get('referring_domains')}** ref domains"
        )
        lines.append("")
        lines.append(
            f"<details><summary>Top in both ({len(both)})</summary>\n\n"
            + "\n".join(f"- {x}" for x in sorted(both)[:25])
            + (f"\n- _…{len(both)-25} more_" if len(both) > 25 else "")
            + "\n\n</details>"
        )
        lines.append("")
        lines.append(
            f"<details><summary>Only in DataForSEO ({len(only_dfs)})</summary>\n\n"
            + "\n".join(f"- {x}" for x in sorted(only_dfs)[:25])
            + (f"\n- _…{len(only_dfs)-25} more_" if len(only_dfs) > 25 else "")
            + "\n\n</details>"
        )
        lines.append("")
        lines.append(
            f"<details><summary>Only in VebAPI ({len(only_veb)})</summary>\n\n"
            + "\n".join(f"- {x}" for x in sorted(only_veb)[:25])
            + (f"\n- _…{len(only_veb)-25} more_" if len(only_veb) > 25 else "")
            + "\n\n</details>"
        )
        lines.append("")

    lines.append("## Verdict heuristic")
    lines.append("")
    coverage_overall = (total_overlap * 100 / total_dfs) if total_dfs else 0
    if coverage_overall >= 50 and total_veb >= total_dfs * 0.8:
        lines.append(
            f"VebAPI hit **{coverage_overall:.0f}%** of DataForSEO's referring-domain index "
            "and surfaced a comparable total volume. **VebAPI is a viable substitute** — "
            "cancel the DataForSEO Backlinks commitment and use VebAPI Scout ($9/mo) instead."
        )
    elif coverage_overall >= 30:
        lines.append(
            f"VebAPI hit **{coverage_overall:.0f}%** of DataForSEO's index. "
            "Marginal — usable for top-level competitor sweeps but DataForSEO is stronger for forensic link work. "
            "Recommend keeping DataForSEO if you need every link; VebAPI Scout if you just need outreach targets."
        )
    else:
        lines.append(
            f"VebAPI's coverage is only **{coverage_overall:.0f}%** of DataForSEO. "
            "Their index is materially thinner — **stay with DataForSEO** for backlinks intelligence."
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", help="comma-separated domain list")
    parser.add_argument(
        "--rows",
        type=int,
        default=200,
        help="referring-domain rows to fetch from each provider",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.domains:
        domains = [normalise_domain(d) for d in args.domains.split(",") if d.strip()]
    else:
        domains = list(DEFAULT_DOMAINS)

    if args.dry_run:
        n = len(domains)
        est_dfs = n * 0.04
        est_veb_credits = n * (1 + max(1, (args.rows + 99) // 100))
        print(f"domains ({n}):")
        for d in domains:
            print(f"  - {d}")
        print(
            f"\nDataForSEO cost: ~${est_dfs:.4f}  •  "
            f"VebAPI credits: {est_veb_credits} (50 free)"
        )
        return 0

    today = date.today().isoformat()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = DATA_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)

    dfs = DataForSEOClient()
    veb = VebAPIClient()

    results: list[dict[str, Any]] = []
    total_dfs_cost = 0.0
    total_veb_credits = 0

    for dom in domains:
        print(f"[cmp] {dom}")
        try:
            dfs_summary, dfs_rd, dfs_cost = dfs_summary_and_refdomains(
                dfs, dom, args.rows
            )
            total_dfs_cost += dfs_cost
            print(
                f"  DFS: {dfs_summary.get('backlinks')} backlinks, "
                f"{len(dfs_rd)} ref domains  cost: ${dfs_cost:.4f}"
            )
        except DataForSEOError as e:
            print(f"  DFS ERROR: {e}", file=sys.stderr)
            dfs_summary, dfs_rd = {}, []

        try:
            veb_summary, veb_rd, veb_credits = veb_summary_and_refdomains(
                veb, dom, args.rows
            )
            total_veb_credits += veb_credits
            print(
                f"  Veb: {veb_summary.get('backlinks')} backlinks, "
                f"{len(veb_rd)} ref domains  credits: {veb_credits}"
            )
        except VebAPIError as e:
            print(f"  Veb ERROR: {e}", file=sys.stderr)
            veb_summary, veb_rd = {}, []

        row = {
            "domain": dom,
            "dfs_summary": dfs_summary,
            "dfs_refdomains": dfs_rd,
            "veb_summary": veb_summary,
            "veb_refdomains": veb_rd,
        }
        results.append(row)
        (out_dir / f"{dom}.json").write_text(json.dumps(row, indent=2), encoding="utf-8")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORT_DIR / f"backlinks-compare-{today}.md"
    out_md.write_text(
        build_report(today, results, total_dfs_cost, total_veb_credits),
        encoding="utf-8",
    )
    print(f"\n[cmp] report: {out_md}")
    print(f"[cmp] DFS cost: ${total_dfs_cost:.4f}  •  Veb credits: {total_veb_credits}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
