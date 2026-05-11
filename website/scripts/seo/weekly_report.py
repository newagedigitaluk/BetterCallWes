"""Weekly SERP report — distils the latest snapshot into a markdown summary.

Reads the most recent JSON from ~/obsidian-vault/Better-Call-Wes/SEO-Data/serp/,
compares to the previous snapshot if one exists, and writes a markdown report
to ~/obsidian-vault/Better-Call-Wes/SEO-Reports/YYYY-MM-DD.md.

Usage:
    python3 website/scripts/seo/weekly_report.py
    python3 website/scripts/seo/weekly_report.py --snapshot 2026-05-11
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "serp"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"

TOP_COMPETITORS = 5


def load_snapshot(stem: str) -> dict[str, Any]:
    path = SNAPSHOT_DIR / f"{stem}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_snapshots() -> list[Path]:
    if not SNAPSHOT_DIR.exists():
        return []
    return sorted(SNAPSHOT_DIR.glob("*.json"))


def _fmt_pos(pos: int | None) -> str:
    return "—" if pos is None else f"#{pos}"


def _first(positions: list[int] | None) -> int | None:
    if not positions:
        return None
    return positions[0]


def section_ranking_changes(curr: dict[str, Any], prev: dict[str, Any] | None) -> str:
    lines = ["## Ranking changes", ""]
    if not prev:
        lines.append("_No previous snapshot — this run is the baseline._")
        return "\n".join(lines) + "\n"

    lines.append(f"_Compared against snapshot from {prev['captured_at']}._")
    lines.append("")
    lines.append("| Query | Organic prev | Organic now | Δ | Local pack prev | Local pack now | Δ |")
    lines.append("|---|---|---|---|---|---|---|")

    for q, curr_q in curr.get("queries", {}).items():
        prev_q = prev.get("queries", {}).get(q) or {}
        if "error" in curr_q or "error" in prev_q:
            lines.append(f"| {q} | error | error | — | — | — | — |")
            continue
        p_org = _first(prev_q.get("our_organic_positions"))
        c_org = _first(curr_q.get("our_organic_positions"))
        p_lp = _first(prev_q.get("our_local_pack_positions"))
        c_lp = _first(curr_q.get("our_local_pack_positions"))
        lines.append(
            f"| {q} | {_fmt_pos(p_org)} | {_fmt_pos(c_org)} | {_delta(p_org, c_org)} "
            f"| {_fmt_pos(p_lp)} | {_fmt_pos(c_lp)} | {_delta(p_lp, c_lp)} |"
        )
    return "\n".join(lines) + "\n"


def _delta(prev: int | None, curr: int | None) -> str:
    if prev is None and curr is None:
        return "—"
    if prev is None:
        return "new"
    if curr is None:
        return "lost"
    d = prev - curr
    if d == 0:
        return "0"
    return f"{'+' if d > 0 else ''}{d}"


def section_local_pack(curr: dict[str, Any]) -> str:
    lines = ["## Local pack presence", ""]
    appears: list[tuple[str, int]] = []
    missing: list[str] = []
    for q, qres in curr.get("queries", {}).items():
        if "error" in qres:
            continue
        positions = qres.get("our_local_pack_positions") or []
        if positions:
            appears.append((q, positions[0]))
        else:
            missing.append(q)

    if appears:
        lines.append("**Appearing in:**")
        lines.append("")
        for q, pos in appears:
            lines.append(f"- {q} — #{pos}")
        lines.append("")
    else:
        lines.append("**Appearing in:** none")
        lines.append("")

    if missing:
        lines.append("**Missing from:**")
        lines.append("")
        for q in missing:
            lines.append(f"- {q}")
        lines.append("")
    return "\n".join(lines) + "\n"


def section_competitors(curr: dict[str, Any]) -> str:
    lines = ["## Top competitors per query", ""]
    for q, qres in curr.get("queries", {}).items():
        if "error" in qres:
            lines.append(f"### {q}")
            lines.append(f"_Error: {qres['error']}_")
            lines.append("")
            continue

        lines.append(f"### {q}")
        lines.append("")

        local_pack = qres.get("local_pack") or []
        if local_pack:
            lines.append("**Local pack (3-pack):**")
            lines.append("")
            for entry in local_pack[:3]:
                title = entry.get("title") or "—"
                domain = entry.get("domain") or ""
                rating = entry.get("rating") or {}
                rv = rating.get("value") if isinstance(rating, dict) else None
                rc = rating.get("votes_count") if isinstance(rating, dict) else None
                rating_str = (
                    f" — {rv}★ ({rc})" if rv is not None and rc is not None else ""
                )
                domain_str = f" [{domain}]" if domain else ""
                lines.append(f"- #{entry.get('rank')} {title}{domain_str}{rating_str}")
            lines.append("")

        organic = qres.get("organic") or []
        if organic:
            lines.append(f"**Top {TOP_COMPETITORS} organic:**")
            lines.append("")
            for entry in organic[:TOP_COMPETITORS]:
                domain = entry.get("domain") or "—"
                title = entry.get("title") or ""
                lines.append(f"- #{entry.get('rank')} {domain} — {title}")
            lines.append("")
    return "\n".join(lines) + "\n"


def section_summary(curr: dict[str, Any]) -> str:
    queries = curr.get("queries", {})
    total = len(queries)
    errors = sum(1 for v in queries.values() if "error" in v)
    organic_hits = sum(
        1 for v in queries.values() if v.get("our_organic_positions")
    )
    lp_hits = sum(1 for v in queries.values() if v.get("our_local_pack_positions"))

    domain_counts: Counter[str] = Counter()
    for v in queries.values():
        if "error" in v:
            continue
        for org in v.get("organic", [])[:10]:
            d = org.get("domain")
            if d:
                domain_counts[d] += 1

    top_domains = domain_counts.most_common(5)

    lines = ["## Summary", ""]
    lines.append(f"- Queries tracked: **{total}**")
    if errors:
        lines.append(f"- Errors: **{errors}**")
    lines.append(f"- We appear in organic results: **{organic_hits} / {total - errors}**")
    lines.append(f"- We appear in local pack: **{lp_hits} / {total - errors}**")
    lines.append(f"- Snapshot cost: **${curr.get('total_cost_usd', 0):.4f}**")
    lines.append("")
    if top_domains:
        lines.append("**Most frequent competitors (top-10 organic across queries):**")
        lines.append("")
        for d, n in top_domains:
            lines.append(f"- {d} — {n}")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_report(curr: dict[str, Any], prev: dict[str, Any] | None) -> str:
    captured = curr.get("captured_at") or date.today().isoformat()
    header = [
        f"# SERP report — {captured}",
        "",
        f"- Location: UK (location_code {curr.get('location_code')}) / {curr.get('se_domain')}",
        f"- Device: {curr.get('device')}  •  Depth: {curr.get('depth')}",
        f"- Our domain: {curr.get('our_domain')}",
        "",
    ]
    body = [
        section_summary(curr),
        section_ranking_changes(curr, prev),
        section_local_pack(curr),
        section_competitors(curr),
    ]
    return "\n".join(header) + "\n" + "\n".join(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot",
        help="snapshot stem (YYYY-MM-DD) — defaults to the most recent",
    )
    args = parser.parse_args()

    snapshots = list_snapshots()
    if not snapshots:
        print("No SERP snapshots found. Run serp_tracker.py first.", file=sys.stderr)
        return 1

    if args.snapshot:
        curr_path = SNAPSHOT_DIR / f"{args.snapshot}.json"
        if not curr_path.exists():
            print(f"Snapshot not found: {curr_path}", file=sys.stderr)
            return 1
    else:
        curr_path = snapshots[-1]

    curr = json.loads(curr_path.read_text(encoding="utf-8"))

    prev_path: Path | None = None
    for p in reversed(snapshots):
        if p == curr_path:
            continue
        prev_path = p
        break
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path else None

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"{curr['captured_at']}.md"
    out.write_text(build_report(curr, prev), encoding="utf-8")
    print(f"[report] written: {out}")
    if prev_path:
        print(f"[report] compared against: {prev_path.name}")
    else:
        print("[report] no previous snapshot — baseline report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
