"""SERP tracker — weekly Google UK ranking snapshots for Better Call Wes.

Runs each priority query through DataForSEO's serp/google/organic/live/advanced
endpoint, captures organic + local pack positions, writes a JSON snapshot to
~/obsidian-vault/Better-Call-Wes/SEO-Data/serp/YYYY-MM-DD.json, and diffs
against the previous snapshot.

Usage:
    python3 website/scripts/seo/serp_tracker.py
    python3 website/scripts/seo/serp_tracker.py --queries plumber\\ Southampton,boiler\\ repair\\ Bitterne
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
SEARCH_ENGINE_DOMAIN = "google.co.uk"
DEFAULT_DEPTH = 30
OUR_DOMAIN = "bettercallwes.co.uk"

CONFIG_PATH = Path(__file__).parent / "queries.json"
SNAPSHOT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "serp"


def load_queries(tier: str = "tier_1_weekly") -> tuple[list[str], str]:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if tier == "tier_2_monthly":
        services = cfg["tier_2_monthly_services"]
        locations = cfg["tier_2_monthly_locations"]
        queries = [
            f"{s} {loc.replace('-', ' ')}" for s in services for loc in locations
        ]
        return queries, cfg.get("our_domain", OUR_DOMAIN)
    if tier in cfg:
        return list(cfg[tier]), cfg.get("our_domain", OUR_DOMAIN)
    raise ValueError(f"Unknown tier: {tier}")


def fetch_serp(client: DataForSEOClient, query: str) -> dict[str, Any]:
    payload = [
        {
            "keyword": query,
            "location_code": UK_LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
            "se_domain": SEARCH_ENGINE_DOMAIN,
            "device": "mobile",
            "os": "android",
            "depth": DEFAULT_DEPTH,
        }
    ]
    return client.post("/v3/serp/google/organic/live/advanced", payload)


def parse_serp(raw: dict[str, Any]) -> dict[str, Any]:
    if not raw.get("tasks"):
        return {"error": "no tasks returned", "raw_status": raw.get("status_message")}
    task = raw["tasks"][0]
    if task.get("status_code") != 20000:
        return {"error": task.get("status_message"), "raw_status": task.get("status_code")}
    results = task.get("result") or []
    if not results:
        return {"error": "empty result"}
    res = results[0]
    items = res.get("items") or []

    organic: list[dict[str, Any]] = []
    local_pack: list[dict[str, Any]] = []
    people_also_ask: list[dict[str, Any]] = []
    related_searches: list[str] = []
    featured_snippet: dict[str, Any] | None = None
    knowledge_graph: dict[str, Any] | None = None
    other_types: list[str] = []
    our_organic_positions: list[int] = []
    our_local_pack_positions: list[int] = []

    for item in items:
        itype = item.get("type")
        if itype == "organic":
            pos = item.get("rank_absolute")
            url = item.get("url") or ""
            domain = (item.get("domain") or "").lower()
            organic.append(
                {
                    "rank": pos,
                    "title": item.get("title"),
                    "url": url,
                    "domain": domain,
                }
            )
            if OUR_DOMAIN in domain:
                our_organic_positions.append(pos)
        elif itype == "local_pack":
            pos = item.get("rank_absolute")
            title = item.get("title") or ""
            domain = (item.get("domain") or "").lower()
            url = item.get("url") or ""
            local_pack.append(
                {
                    "rank": pos,
                    "title": title,
                    "domain": domain,
                    "url": url,
                    "rating": item.get("rating"),
                }
            )
            if OUR_DOMAIN in domain or "better call wes" in title.lower():
                our_local_pack_positions.append(pos)
        elif itype == "people_also_ask":
            for paa in item.get("items") or []:
                if paa.get("type") != "people_also_ask_element":
                    continue
                exp = paa.get("expanded_element") or []
                first = exp[0] if exp else {}
                people_also_ask.append(
                    {
                        "question": paa.get("title"),
                        "answer_source_domain": (first.get("domain") or "").lower(),
                        "answer_url": first.get("url"),
                        "answer_snippet": first.get("description"),
                    }
                )
        elif itype in ("related_searches", "people_also_search"):
            for term in item.get("items") or []:
                if isinstance(term, str):
                    related_searches.append(term)
                elif isinstance(term, dict) and term.get("title"):
                    related_searches.append(term["title"])
        elif itype == "featured_snippet":
            featured_snippet = {
                "rank": item.get("rank_absolute"),
                "title": item.get("title"),
                "url": item.get("url"),
                "domain": (item.get("domain") or "").lower(),
                "description": item.get("description"),
            }
            other_types.append(itype)
        elif itype == "knowledge_graph":
            knowledge_graph = {
                "title": item.get("title"),
                "subtitle": item.get("sub_title"),
                "description": item.get("description"),
            }
            other_types.append(itype)
        else:
            other_types.append(itype)

    return {
        "se_results_count": res.get("se_results_count"),
        "items_count": res.get("items_count"),
        "organic": organic,
        "local_pack": local_pack,
        "people_also_ask": people_also_ask,
        "related_searches": sorted(set(related_searches)),
        "featured_snippet": featured_snippet,
        "knowledge_graph": knowledge_graph,
        "other_feature_types": sorted(set(other_types)),
        "our_organic_positions": our_organic_positions,
        "our_local_pack_positions": our_local_pack_positions,
    }


def run_snapshot(queries: list[str]) -> dict[str, Any]:
    client = DataForSEOClient()
    snapshot: dict[str, Any] = {
        "captured_at": date.today().isoformat(),
        "location_code": UK_LOCATION_CODE,
        "language_code": LANGUAGE_CODE,
        "se_domain": SEARCH_ENGINE_DOMAIN,
        "device": "mobile",
        "depth": DEFAULT_DEPTH,
        "our_domain": OUR_DOMAIN,
        "queries": {},
        "total_cost_usd": 0.0,
    }

    for q in queries:
        print(f"[serp] fetching: {q}")
        try:
            raw = fetch_serp(client, q)
        except DataForSEOError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            snapshot["queries"][q] = {"error": str(e)}
            continue
        cost = float(raw.get("cost") or 0)
        snapshot["total_cost_usd"] += cost
        parsed = parse_serp(raw)
        parsed["cost_usd"] = cost
        snapshot["queries"][q] = parsed
        if "error" in parsed:
            print(f"  ERROR: {parsed['error']}", file=sys.stderr)
        else:
            org = parsed["our_organic_positions"]
            lp = parsed["our_local_pack_positions"]
            print(
                f"  organic items: {len(parsed['organic'])}  "
                f"local pack: {len(parsed['local_pack'])}  "
                f"our organic: {org or '—'}  our local pack: {lp or '—'}  "
                f"cost: ${cost:.4f}"
            )

    return snapshot


def latest_previous_snapshot(today: str) -> tuple[Path, dict[str, Any]] | None:
    if not SNAPSHOT_DIR.exists():
        return None
    candidates = sorted(p for p in SNAPSHOT_DIR.glob("*.json") if p.stem != today)
    if not candidates:
        return None
    prev = candidates[-1]
    try:
        return prev, json.loads(prev.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def diff_positions(prev: dict[str, Any], curr: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for q, curr_q in curr.get("queries", {}).items():
        prev_q = prev.get("queries", {}).get(q)
        if not prev_q or "error" in curr_q or "error" in prev_q:
            continue
        prev_org = (prev_q.get("our_organic_positions") or [None])[0]
        curr_org = (curr_q.get("our_organic_positions") or [None])[0]
        prev_lp = (prev_q.get("our_local_pack_positions") or [None])[0]
        curr_lp = (curr_q.get("our_local_pack_positions") or [None])[0]
        if prev_org != curr_org:
            lines.append(f"  organic  '{q}': {_fmt(prev_org)} -> {_fmt(curr_org)}")
        if prev_lp != curr_lp:
            lines.append(f"  local    '{q}': {_fmt(prev_lp)} -> {_fmt(curr_lp)}")
    return lines


def _fmt(pos: int | None) -> str:
    return "—" if pos is None else f"#{pos}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        help="comma-separated query list (overrides tier config)",
    )
    parser.add_argument(
        "--tier",
        default="tier_1_weekly",
        help="tier key from queries.json (default: tier_1_weekly)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the query list and exit without spending credits",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="merge new queries into today's existing snapshot instead of overwriting",
    )
    args = parser.parse_args()

    if args.queries:
        queries = [q.strip() for q in args.queries.split(",") if q.strip()]
    else:
        queries, _ = load_queries(args.tier)

    if args.dry_run:
        print(f"tier: {args.tier}  count: {len(queries)}")
        for q in queries:
            print(f"  - {q}")
        print(f"\nestimated cost: ${len(queries) * 0.005:.4f}")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_path = SNAPSHOT_DIR / f"{today}.json"

    prev = latest_previous_snapshot(today)

    if args.merge and out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        already = set(existing.get("queries", {}).keys())
        queries = [q for q in queries if q not in already]
        if not queries:
            print("[serp] all queries already in today's snapshot — nothing to do")
            return 0
        print(f"[serp] merging {len(queries)} new queries into {out_path.name}")
        new = run_snapshot(queries)
        existing.setdefault("queries", {}).update(new["queries"])
        existing["total_cost_usd"] = (
            existing.get("total_cost_usd", 0) + new["total_cost_usd"]
        )
        snapshot = existing
    else:
        snapshot = run_snapshot(queries)
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"\n[serp] snapshot written: {out_path}")
    print(f"[serp] total cost: ${snapshot['total_cost_usd']:.4f}")

    if prev:
        prev_path, prev_data = prev
        changes = diff_positions(prev_data, snapshot)
        print(f"\n[diff] vs {prev_path.name}:")
        if changes:
            print("\n".join(changes))
        else:
            print("  no position changes")
    else:
        print("\n[diff] no previous snapshot — baseline established")

    return 0


if __name__ == "__main__":
    sys.exit(main())
