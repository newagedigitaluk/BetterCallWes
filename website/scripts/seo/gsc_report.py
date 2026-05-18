"""Read the latest GSC snapshot and write a markdown analysis to
~/obsidian-vault/Better-Call-Wes/SEO-Reports/gsc-YYYY-MM-DD.md.

Picks out the things that actually drive decisions:
  - Top pages by impressions, with avg position + CTR
  - Top queries with their primary ranking page
  - Near-page-1 wins (queries at positions 11–20)
  - Position-1 zero-CTR queries (snippet problems)
  - Multi-page queries (cannibalization)

Usage:
    python3 website/scripts/seo/gsc_report.py
    python3 website/scripts/seo/gsc_report.py --snapshot 2026-05-13
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

DATA = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "gsc"
REPORTS = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"
SITE = "https://bettercallwes.co.uk"


def short_url(u: str) -> str:
    return u.replace(SITE, "") or "/"


def latest_snapshot() -> Path | None:
    if not DATA.exists():
        return None
    snaps = sorted(p for p in DATA.iterdir() if p.is_dir())
    return snaps[-1] if snaps else None


def load(snap: Path) -> dict:
    pages = json.loads((snap / "pages.json").read_text())
    queries = json.loads((snap / "queries.json").read_text())
    cross = json.loads((snap / "queries-by-page.json").read_text())
    return {"pages": pages, "queries": queries, "cross": cross}


def section_pages(d: dict) -> str:
    rows = d["pages"]["rows"]
    lines = [
        "## Pages — top 25 by impressions",
        "",
        "| URL | Impressions | Clicks | CTR | Avg pos |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows[:25]:
        lines.append(
            f"| `{short_url(r['keys'][0])}` | {r['impressions']:,} | {r['clicks']} "
            f"| {r['ctr']*100:.2f}% | {r['position']:.1f} |"
        )
    return "\n".join(lines) + "\n"


def section_queries(d: dict, cross: list[dict]) -> str:
    # Build query → primary ranking page (the page with the most impressions for it)
    pg_for_q: dict[str, str] = {}
    pg_imp: dict[str, int] = {}
    for r in cross:
        q, p = r["keys"]
        if r["impressions"] > pg_imp.get(q, -1):
            pg_imp[q] = r["impressions"]
            pg_for_q[q] = p

    rows = d["queries"]["rows"]
    lines = [
        "## Queries — top 30 by impressions",
        "",
        "| Query | Impressions | Clicks | CTR | Avg pos | Primary page |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in rows[:30]:
        q = r["keys"][0]
        page = short_url(pg_for_q.get(q, ""))
        lines.append(
            f"| {q} | {r['impressions']:,} | {r['clicks']} "
            f"| {r['ctr']*100:.2f}% | {r['position']:.1f} | `{page}` |"
        )
    return "\n".join(lines) + "\n"


def section_near_wins(d: dict) -> str:
    """Queries at positions 11–20 with >=20 impressions = page-2 wins to push."""
    rows = [
        r
        for r in d["queries"]["rows"]
        if 11 <= r["position"] <= 20 and r["impressions"] >= 20
    ]
    rows.sort(key=lambda r: r["position"])
    if not rows:
        return "## Near wins (position 11–20)\n\n_None right now._\n"
    lines = [
        "## Near wins — queries at positions 11–20 with ≥20 impressions",
        "",
        "_Pushing any of these to top 10 should produce real click gains._",
        "",
        "| Query | Impressions | Avg pos | Suggests |",
        "|---|---:|---:|---|",
    ]
    for r in rows[:30]:
        lines.append(
            f"| {r['keys'][0]} | {r['impressions']:,} | {r['position']:.1f} "
            f"| internal links + intent-led title |"
        )
    return "\n".join(lines) + "\n"


def section_snippet_problems(d: dict) -> str:
    """Top-10 ranking queries with very low CTR — snippets aren't earning the click."""
    rows = [
        r
        for r in d["queries"]["rows"]
        if r["position"] <= 10 and r["impressions"] >= 50 and r["ctr"] < 0.02
    ]
    rows.sort(key=lambda r: -r["impressions"])
    if not rows:
        return "## Snippet problems\n\n_No top-10 queries with low CTR found._\n"
    lines = [
        "## Snippet problems — top-10 queries with under-2% CTR",
        "",
        "_You rank well but nobody clicks. Most likely fix: rewrite the page's "
        "`<title>` and meta description to match the query intent._",
        "",
        "| Query | Impressions | Position | CTR | Expected CTR |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows[:20]:
        expected = {1: 30, 2: 20, 3: 15, 4: 10, 5: 8, 6: 6, 7: 5, 8: 4, 9: 3, 10: 2.5}
        exp = expected.get(int(round(r["position"])), 1.5)
        lines.append(
            f"| {r['keys'][0]} | {r['impressions']:,} | {r['position']:.1f} "
            f"| **{r['ctr']*100:.2f}%** | ~{exp}% |"
        )
    return "\n".join(lines) + "\n"


def section_cannibalization(d: dict) -> str:
    """Find queries where 2+ pages get meaningful impressions = cannibalization."""
    by_query: dict[str, list[dict]] = defaultdict(list)
    for r in d["cross"]["rows"]:
        if r["impressions"] >= 30:
            q, p = r["keys"]
            by_query[q].append({"page": p, **r})
    competing = [
        (q, pgs)
        for q, pgs in by_query.items()
        if len(pgs) >= 2 and sum(p["impressions"] for p in pgs) >= 100
    ]
    competing.sort(key=lambda x: -sum(p["impressions"] for p in x[1]))
    if not competing:
        return "## Cannibalisation\n\n_No multi-page cannibalisation detected._\n"
    lines = [
        "## Cannibalisation — multiple pages ranking for the same query",
        "",
        "_The page Google should consolidate around is usually the higher-position one. "
        "Either differentiate the other page so it targets distinct queries, or 301-redirect it._",
        "",
        "| Query | Page | Imp | Pos |",
        "|---|---|---:|---:|",
    ]
    for q, pgs in competing[:15]:
        pgs.sort(key=lambda p: p["position"])
        for i, pg in enumerate(pgs[:3]):
            shown_q = q if i == 0 else ""
            lines.append(
                f"| {shown_q} | `{short_url(pg['page'])}` | {pg['impressions']:,} | {pg['position']:.1f} |"
            )
    return "\n".join(lines) + "\n"


def build_report(snap_date: str, d: dict) -> str:
    p_rows = d["pages"]["rows"]
    q_rows = d["queries"]["rows"]
    total_clicks = sum(r["clicks"] for r in p_rows)
    total_imp = sum(r["impressions"] for r in p_rows)
    ctr = (total_clicks / total_imp * 100) if total_imp else 0
    avg_pos = (
        sum(r["position"] * r["impressions"] for r in p_rows) / total_imp
        if total_imp
        else 0
    )

    lines = [
        f"# GSC report — {snap_date}",
        "",
        f"- Window: **{d['pages']['start']} → {d['pages']['end']}**",
        f"- Total impressions: **{total_imp:,}**  •  Total clicks: **{total_clicks:,}**  "
        f"•  CTR: **{ctr:.2f}%**",
        f"- Impression-weighted average position: **{avg_pos:.1f}**",
        f"- Indexed pages with impressions: **{len(p_rows)}**",
        f"- Distinct queries: **{len(q_rows)}**",
        "",
        section_pages(d),
        section_queries(d, d["cross"]["rows"]),
        section_near_wins(d),
        section_snippet_problems(d),
        section_cannibalization(d),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", help="YYYY-MM-DD (defaults to latest)")
    args = parser.parse_args()

    if args.snapshot:
        snap = DATA / args.snapshot
    else:
        snap = latest_snapshot()
    if snap is None or not snap.exists():
        print("No GSC snapshots. Run: python3 website/scripts/seo/gsc_pull.py")
        return 1

    d = load(snap)
    report = build_report(snap.name, d)

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"gsc-{date.today().isoformat()}.md"
    out.write_text(report, encoding="utf-8")
    print(f"Report written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
