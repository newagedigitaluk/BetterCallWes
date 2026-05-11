"""People Also Ask + related-search harvester.

Aggregates PAA questions, related searches, and featured snippet ownership
across all SERP snapshots in ~/obsidian-vault/Better-Call-Wes/SEO-Data/serp/
and writes a content-gap report to ~/obsidian-vault/Better-Call-Wes/SEO-Reports/
content-gaps-YYYY-MM-DD.md.

No API spend — reads from already-captured snapshots.

Usage:
    python3 website/scripts/seo/paa_harvester.py
    python3 website/scripts/seo/paa_harvester.py --since 2026-05-01
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "serp"
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"
OUR_DOMAIN = "bettercallwes.co.uk"


def _norm_question(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def _norm_search(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def load_snapshots(since: str | None) -> list[dict[str, Any]]:
    snaps = []
    if not SNAPSHOT_DIR.exists():
        return snaps
    for path in sorted(SNAPSHOT_DIR.glob("*.json")):
        if since and path.stem < since:
            continue
        try:
            snaps.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return snaps


def harvest(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    paa_questions: Counter[str] = Counter()
    paa_examples: dict[str, str] = {}
    paa_queries_seen: dict[str, set[str]] = defaultdict(set)
    paa_answer_domains: dict[str, Counter[str]] = defaultdict(Counter)

    related: Counter[str] = Counter()
    related_examples: dict[str, str] = {}
    related_queries_seen: dict[str, set[str]] = defaultdict(set)

    fs_owners: Counter[str] = Counter()
    fs_unowned_queries: list[tuple[str, str | None]] = []

    for snap in snapshots:
        for query, qres in snap.get("queries", {}).items():
            if "error" in qres:
                continue

            for entry in qres.get("people_also_ask") or []:
                question = entry.get("question") or ""
                if not question:
                    continue
                norm = _norm_question(question)
                paa_questions[norm] += 1
                paa_examples.setdefault(norm, question)
                paa_queries_seen[norm].add(query)
                domain = entry.get("answer_source_domain") or ""
                if domain:
                    paa_answer_domains[norm][domain] += 1

            for term in qres.get("related_searches") or []:
                norm = _norm_search(term)
                related[norm] += 1
                related_examples.setdefault(norm, term)
                related_queries_seen[norm].add(query)

            fs = qres.get("featured_snippet")
            if fs:
                domain = (fs.get("domain") or "").lower()
                if domain:
                    fs_owners[domain] += 1
                fs_unowned_queries.append((query, fs.get("url")))

    return {
        "paa_questions": paa_questions,
        "paa_examples": paa_examples,
        "paa_queries_seen": paa_queries_seen,
        "paa_answer_domains": paa_answer_domains,
        "related": related,
        "related_examples": related_examples,
        "related_queries_seen": related_queries_seen,
        "fs_owners": fs_owners,
        "fs_queries": fs_unowned_queries,
        "snapshot_count": len(snapshots),
        "date_range": (
            (snapshots[0].get("captured_at"), snapshots[-1].get("captured_at"))
            if snapshots
            else (None, None)
        ),
    }


def build_report(data: dict[str, Any]) -> str:
    today = date.today().isoformat()
    start, end = data["date_range"]
    lines = [
        f"# Content gaps — {today}",
        "",
        f"_Aggregated from {data['snapshot_count']} SERP snapshot(s)"
        + (f", {start} → {end}" if start else "")
        + "._",
        "",
    ]

    paa = data["paa_questions"]
    lines.append("## People Also Ask — top questions")
    lines.append("")
    if paa:
        lines.append("Use these as FAQ candidates and structured-data Q&A blocks.")
        lines.append("")
        lines.append("| Question | Appears | Queries triggering it | Top answer domains |")
        lines.append("|---|---|---|---|")
        for norm, count in paa.most_common(40):
            label = data["paa_examples"][norm]
            triggers = ", ".join(sorted(data["paa_queries_seen"][norm])[:3])
            top_doms = data["paa_answer_domains"][norm].most_common(3)
            doms_str = ", ".join(f"{d} ({n})" for d, n in top_doms) or "—"
            owns = " **(us)**" if OUR_DOMAIN in {d for d, _ in top_doms} else ""
            lines.append(f"| {label}{owns} | {count} | {triggers} | {doms_str} |")
    else:
        lines.append("_No PAA captured yet._")
    lines.append("")

    rel = data["related"]
    lines.append("## Related searches — keyword expansion candidates")
    lines.append("")
    if rel:
        lines.append(
            "Cross-reference with `keyword_volumes.py` to pick the high-volume ones."
        )
        lines.append("")
        lines.append("| Term | Appears | Triggered by |")
        lines.append("|---|---|---|")
        for norm, count in rel.most_common(60):
            label = data["related_examples"][norm]
            triggers = ", ".join(sorted(data["related_queries_seen"][norm])[:3])
            lines.append(f"| {label} | {count} | {triggers} |")
    else:
        lines.append("_No related searches captured yet._")
    lines.append("")

    fs = data["fs_owners"]
    lines.append("## Featured snippets")
    lines.append("")
    if fs:
        ours = fs.get(OUR_DOMAIN, 0)
        total = sum(fs.values())
        lines.append(
            f"- Total featured snippets across snapshots: **{total}**"
            f"  •  Owned by us: **{ours}**"
        )
        lines.append("")
        lines.append("**Owners:**")
        for dom, n in fs.most_common(10):
            tag = " **(us)**" if dom == OUR_DOMAIN else ""
            lines.append(f"- {dom}{tag} — {n}")
    else:
        lines.append("_No featured snippets present for the tracked queries._")
    lines.append("")

    lines.append("## Action checklist")
    lines.append("")
    lines.append(
        "- [ ] For each top PAA question, confirm we have an FAQ entry or short answer block on the most relevant service or location page."
    )
    lines.append(
        "- [ ] Add JSON-LD `FAQPage` schema to pages that answer 3+ PAA questions."
    )
    lines.append(
        "- [ ] Pick 5 related-search terms that are not yet site keywords and brief content for the relevant location/service page."
    )
    lines.append(
        "- [ ] For featured snippets we don't own, study the current owner's answer format (paragraph, list, table) and write a tighter version."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--since",
        help="only include snapshots dated >= YYYY-MM-DD",
    )
    parser.add_argument(
        "--output",
        help="override output path",
    )
    args = parser.parse_args()

    snapshots = load_snapshots(args.since)
    if not snapshots:
        print("No snapshots found. Run serp_tracker.py first.", file=sys.stderr)
        return 1

    data = harvest(snapshots)
    report = build_report(data)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.output) if args.output else REPORT_DIR / f"content-gaps-{date.today().isoformat()}.md"
    out.write_text(report, encoding="utf-8")
    print(f"[paa] written: {out}")
    print(
        f"[paa] {len(data['paa_questions'])} unique PAA questions, "
        f"{len(data['related'])} unique related searches, "
        f"{sum(data['fs_owners'].values())} featured snippets"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
