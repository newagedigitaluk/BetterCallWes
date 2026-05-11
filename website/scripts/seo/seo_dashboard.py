"""SEO executive dashboard — single weekly markdown that consolidates
everything: ranking position, local pack presence, content gaps,
competitor activity, onpage issues, and a prioritised action list.

Reads from the most recent files in:
    SEO-Data/serp/
    SEO-Data/volumes/
    SEO-Data/onpage/<date>/
    SEO-Data/competitors/<date>/

Writes:
    SEO-Reports/dashboard-YYYY-MM-DD.md

Usage:
    python3 website/scripts/seo/seo_dashboard.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

VAULT = Path.home() / "obsidian-vault" / "Better-Call-Wes"
SERP_DIR = VAULT / "SEO-Data" / "serp"
VOLUMES_DIR = VAULT / "SEO-Data" / "volumes"
ONPAGE_DIR = VAULT / "SEO-Data" / "onpage"
COMPETITOR_DIR = VAULT / "SEO-Data" / "competitors"
REPORT_DIR = VAULT / "SEO-Reports"
OUR_DOMAIN = "bettercallwes.co.uk"


def latest_file(directory: Path, pattern: str = "*.json") -> Path | None:
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def latest_dir(parent: Path) -> Path | None:
    if not parent.exists():
        return None
    subs = sorted(p for p in parent.iterdir() if p.is_dir())
    return subs[-1] if subs else None


def load_serp() -> dict[str, Any] | None:
    p = latest_file(SERP_DIR)
    return json.loads(p.read_text(encoding="utf-8")) if p else None


def load_volumes() -> list[dict[str, Any]]:
    if not VOLUMES_DIR.exists():
        return []
    out = []
    for p in sorted(VOLUMES_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def load_onpage() -> list[dict[str, Any]]:
    d = latest_dir(ONPAGE_DIR)
    if not d:
        return []
    rows = []
    for p in sorted(d.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows.append(data.get("parsed") or {})
    return rows


def load_competitors() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    d = latest_dir(COMPETITOR_DIR)
    if not d:
        return [], {}
    our: list[dict[str, Any]] = []
    comp: dict[str, list[dict[str, Any]]] = {}
    for p in sorted(d.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        dom = data.get("domain") or p.stem
        rows = data.get("rows") or []
        if dom == OUR_DOMAIN:
            our = rows
        else:
            comp[dom] = rows
    return our, comp


def section_headline(serp: dict[str, Any] | None) -> str:
    if not serp:
        return "_No SERP snapshot yet._\n"
    queries = serp.get("queries") or {}
    valid = [q for q, v in queries.items() if "error" not in v]
    organic = sum(1 for q in valid if queries[q].get("our_organic_positions"))
    lp = sum(1 for q in valid if queries[q].get("our_local_pack_positions"))
    return (
        f"- Queries tracked: **{len(valid)}**\n"
        f"- We appear in organic top-30: **{organic} ({organic*100//max(1,len(valid))}%)**\n"
        f"- We appear in local pack 3-pack: **{lp} ({lp*100//max(1,len(valid))}%)**\n"
        f"- Snapshot captured: **{serp.get('captured_at')}**\n"
    )


def section_priority_wins(
    serp: dict[str, Any] | None, volumes: list[dict[str, Any]]
) -> str:
    if not serp:
        return ""
    queries = serp.get("queries") or {}
    vol_lookup: dict[str, dict[str, Any]] = {}
    for v in volumes:
        for r in v.get("rows") or []:
            kw = (r.get("keyword") or "").lower()
            if kw:
                vol_lookup[kw] = r

    rows: list[dict[str, Any]] = []
    for q, qres in queries.items():
        if "error" in qres:
            continue
        org_pos = (qres.get("our_organic_positions") or [None])[0]
        lp_pos = (qres.get("our_local_pack_positions") or [None])[0]
        vol_row = vol_lookup.get(q.lower(), {})
        rows.append(
            {
                "query": q,
                "organic": org_pos,
                "local_pack": lp_pos,
                "volume": vol_row.get("search_volume"),
                "cpc": vol_row.get("cpc"),
            }
        )

    def opportunity_score(r: dict[str, Any]) -> float:
        vol = r.get("volume") or 0
        org = r.get("organic")
        lp = r.get("local_pack")
        in_pack = lp is not None
        if org is None and not in_pack:
            return vol * 1.0
        if org is None or org > 20:
            return vol * 0.7
        if 11 <= org <= 20:
            return vol * 0.5
        if 4 <= org <= 10:
            return vol * 0.3
        return vol * 0.05

    rows.sort(key=opportunity_score, reverse=True)
    top = [r for r in rows if (r.get("volume") or 0) > 0][:15]

    if not top:
        return "_No volume-bearing opportunities found in current tier set._\n"

    lines = [
        "| Query | Vol/mo | Our organic | Our local pack | CPC | Opportunity |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in top:
        score = opportunity_score(r)
        cpc = f"£{r['cpc']:.2f}" if isinstance(r.get("cpc"), (int, float)) else "—"
        org = f"#{r['organic']}" if r.get("organic") else "—"
        lp = f"#{r['local_pack']}" if r.get("local_pack") else "—"
        lines.append(
            f"| {r['query']} | {r.get('volume') or '—'} | {org} | {lp} | {cpc} | {score:.0f} |"
        )
    return "\n".join(lines) + "\n"


def section_local_pack(serp: dict[str, Any] | None) -> str:
    if not serp:
        return ""
    in_lp: list[tuple[str, int]] = []
    not_in_lp: list[str] = []
    for q, v in (serp.get("queries") or {}).items():
        if "error" in v:
            continue
        pos = v.get("our_local_pack_positions") or []
        if pos:
            in_lp.append((q, pos[0]))
        else:
            not_in_lp.append(q)
    lines = []
    lines.append(f"**Appearing ({len(in_lp)}):**\n")
    if in_lp:
        for q, p in sorted(in_lp, key=lambda x: x[1]):
            lines.append(f"- #{p} — {q}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append(f"**Missing ({len(not_in_lp)}):**\n")
    lines.extend(f"- {q}" for q in not_in_lp[:30])
    if len(not_in_lp) > 30:
        lines.append(f"- _...and {len(not_in_lp) - 30} more_")
    return "\n".join(lines) + "\n"


def section_competitor_gaps(
    our_rows: list[dict[str, Any]], competitor: dict[str, list[dict[str, Any]]]
) -> str:
    if not competitor:
        return "_No competitor data yet — run `competitor_intel.py`._\n"
    our_kw = {(r.get("keyword") or "").lower() for r in our_rows if r.get("keyword")}
    gap: dict[str, dict[str, Any]] = {}
    for dom, rows in competitor.items():
        for r in rows:
            kw = (r.get("keyword") or "").lower()
            if not kw or kw in our_kw:
                continue
            entry = gap.setdefault(
                kw,
                {
                    "keyword": r["keyword"],
                    "vol": r.get("search_volume") or 0,
                    "cpc": r.get("cpc"),
                    "rivals": [],
                },
            )
            entry["rivals"].append((dom, r.get("rank") or 99))

    ordered = sorted(
        gap.values(),
        key=lambda x: (-(x["vol"] or 0), -len(x["rivals"])),
    )[:15]
    if not ordered:
        return "_No content gaps surfaced._\n"
    lines = ["| Keyword | Vol/mo | CPC | Top competitor |", "|---|---:|---:|---|"]
    for g in ordered:
        top_rival = min(g["rivals"], key=lambda x: x[1])
        cpc = f"£{g['cpc']:.2f}" if isinstance(g.get("cpc"), (int, float)) else "—"
        lines.append(
            f"| {g['keyword']} | {g['vol']} | {cpc} | {top_rival[0]} #{top_rival[1]} |"
        )
    return "\n".join(lines) + "\n"


def section_onpage(onpage: list[dict[str, Any]]) -> str:
    if not onpage:
        return "_No onpage data yet._\n"
    ok = [p for p in onpage if "error" not in p and p.get("status_code") == 200]
    broken = [p for p in onpage if p.get("status_code") and p["status_code"] >= 400]
    issue_counts: dict[str, int] = {}
    for p in ok:
        for issue in p.get("issues_present") or []:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    lines = [
        f"- Pages audited: **{len(onpage)}**  •  OK: **{len(ok)}**  •  Broken (4xx/5xx): **{len(broken)}**",
        "",
    ]
    if broken:
        lines.append("**Broken pages — fix urgently:**\n")
        for p in broken:
            lines.append(f"- {p['url']} → {p.get('status_code')}")
        lines.append("")
    if issue_counts:
        lines.append("**Most common issues:**\n")
        lines.append("| Issue | Pages |")
        lines.append("|---|---:|")
        for k, v in sorted(issue_counts.items(), key=lambda kv: -kv[1])[:8]:
            lines.append(f"| {k} | {v} |")
    return "\n".join(lines) + "\n"


def section_actions(
    serp: dict[str, Any] | None,
    onpage: list[dict[str, Any]],
    competitor: dict[str, list[dict[str, Any]]],
) -> str:
    actions: list[str] = []
    if onpage:
        broken = [p for p in onpage if p.get("status_code") and p["status_code"] >= 400]
        if broken:
            actions.append(
                f"Fix the {len(broken)} broken page(s): "
                + ", ".join(p["url"] for p in broken[:3])
                + ("…" if len(broken) > 3 else "")
            )
        long_titles = [p for p in onpage if (p.get("title_length") or 0) > 60]
        if long_titles:
            actions.append(
                f"Rewrite {len(long_titles)} page titles >60 chars (most location pages are 65–71 chars)."
            )
    if serp:
        missing_lp = [
            q
            for q, v in (serp.get("queries") or {}).items()
            if "error" not in v and not v.get("our_local_pack_positions")
        ]
        if missing_lp:
            actions.append(
                f"GBP work: we're missing from {len(missing_lp)} local packs. "
                f"Verify service area is set for SO14–SO51, add weekly photos, request reviews from recent customers."
            )
    if competitor:
        top_rival = max(competitor.items(), key=lambda kv: len(kv[1]))[0]
        actions.append(
            f"Mirror the top topical pages of {top_rival} — they have the most keywords ranking in top 20."
        )
    actions.append(
        "Add an FAQ block to the homepage, pricing page, and each service page using the People Also Ask questions in `content-gaps-*.md`."
    )
    actions.append(
        "Outreach: list on Checkatrade, Trustpilot, Yell, Bark, MyBuilder, RatedPeople if not already (citations + minor backlinks)."
    )
    return "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions)) + "\n"


def build_dashboard(
    serp: dict[str, Any] | None,
    volumes: list[dict[str, Any]],
    onpage: list[dict[str, Any]],
    our_rows: list[dict[str, Any]],
    competitor: dict[str, list[dict[str, Any]]],
) -> str:
    today = date.today().isoformat()
    sections = [
        f"# SEO dashboard — {today}",
        "",
        "## Headline",
        "",
        section_headline(serp),
        "## Priority wins (volume × ranking gap)",
        "",
        section_priority_wins(serp, volumes),
        "## Local pack presence",
        "",
        section_local_pack(serp),
        "## Top content gaps (competitors rank, we don't)",
        "",
        section_competitor_gaps(our_rows, competitor),
        "## On-page health",
        "",
        section_onpage(onpage),
        "## This week's action plan",
        "",
        section_actions(serp, onpage, competitor),
    ]
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="override output path")
    args = parser.parse_args()

    serp = load_serp()
    volumes = load_volumes()
    onpage = load_onpage()
    our_rows, competitor = load_competitors()

    md = build_dashboard(serp, volumes, onpage, our_rows, competitor)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.output) if args.output else REPORT_DIR / f"dashboard-{date.today().isoformat()}.md"
    out.write_text(md, encoding="utf-8")
    print(f"[dash] written: {out}")
    print(
        f"[dash] sources — "
        f"serp: {'✓' if serp else '✗'}  "
        f"volumes: {len(volumes)}  "
        f"onpage: {len(onpage)} pages  "
        f"competitors: {len(competitor)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
