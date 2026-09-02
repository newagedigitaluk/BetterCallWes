"""Geo-grid rank map — where does Better Call Wes actually rank on Google Maps?

Every other script in this folder asks "where do we rank in Southampton?", which
is a single point (the city centroid). Local pack rankings decay with distance
from the business address, so that one number hides the thing that matters:
how far out the visibility actually reaches.

This runs the same keyword through DataForSEO's Google Maps endpoint at every
point of a lat/long grid centred on the business, and renders the resulting rank
at each point. Same idea as Local Falcon / BrightLocal geo-grids.

Cost: ~$0.002 per grid point (7x7 = 49 points ~= $0.10 per keyword per run).
ALWAYS --dry-run first.

Usage:
  python3 geo_grid.py --keyword "boiler repair southampton" --dry-run
  python3 geo_grid.py --keyword "boiler repair southampton" --date 2026-08-04
  python3 geo_grid.py --keyword "plumber southampton" --size 5 --spacing 2.0

Outputs (when --date given, else 'latest/'):
  Data:   ~/obsidian-vault/Better-Call-Wes/SEO-Data/geogrid/<date>/<slug>.json
  Report: ~/obsidian-vault/Better-Call-Wes/SEO-Reports/geogrid-<date>-<slug>.md
  Visual: ~/obsidian-vault/Better-Call-Wes/SEO-Reports/geogrid-<date>-<slug>.html
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from dataforseo_client import DataForSEOClient, DataForSEOError

# 52 Manor Farm Road, Southampton SO18 1NQ — the LSA/GBP registered address.
HOME_LAT = 50.9186
HOME_LNG = -1.3719
OUR_NAME_MATCH = "better call wes"
OUR_DOMAIN = "bettercallwes.co.uk"

LANGUAGE_CODE = "en"
# Zoom is a viewport, not a search radius. At 15 the box is so tight that only a
# handful of businesses fall inside it, so Google returns 0-3 results (and the
# cramped query is also ~3x slower). 12 reliably returns a full result set.
# Omitting zoom altogether returns "No Search Results".
ZOOM = 12
DEPTH = 20
COST_PER_POINT = 0.002
# Each point is an independent live scrape (~3-7s), so run them concurrently.
MAX_WORKERS = 8

MILES_PER_DEG_LAT = 69.0
OUT_DATA = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "geogrid"
OUT_REPORTS = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"


def build_grid(size: int, spacing_miles: float) -> list[dict[str, Any]]:
    """Square grid of (row, col, lat, lng), centred on the business."""
    d_lat = spacing_miles / MILES_PER_DEG_LAT
    d_lng = spacing_miles / (MILES_PER_DEG_LAT * math.cos(math.radians(HOME_LAT)))
    half = size // 2
    points = []
    for row in range(size):
        for col in range(size):
            # row 0 = north (top of the map), so latitude descends as row grows
            points.append({
                "row": row,
                "col": col,
                "lat": round(HOME_LAT + (half - row) * d_lat, 6),
                "lng": round(HOME_LNG + (col - half) * d_lng, 6),
            })
    return points


def fetch_point(client: DataForSEOClient, keyword: str, lat: float, lng: float) -> dict[str, Any]:
    payload = [{
        "keyword": keyword,
        "location_coordinate": f"{lat},{lng},{ZOOM}",
        "language_code": LANGUAGE_CODE,
        "device": "mobile",
        "depth": DEPTH,
    }]
    return client.post("/v3/serp/google/maps/live/advanced", payload)


def parse_point(raw: dict[str, Any]) -> dict[str, Any]:
    """Pull our rank + the businesses beating us out of one Maps response."""
    tasks = raw.get("tasks") or []
    if not tasks or tasks[0].get("status_code") != 20000:
        msg = tasks[0].get("status_message") if tasks else raw.get("status_message")
        return {"error": msg or "no task"}
    results = tasks[0].get("result") or []
    if not results:
        return {"error": "empty result"}
    items = results[0].get("items") or []

    our_rank = None
    top = []
    for it in items:
        rank = it.get("rank_absolute")
        title = (it.get("title") or "").strip()
        domain = (it.get("domain") or "").strip()
        if len(top) < 3:
            top.append({"rank": rank, "title": title, "domain": domain})
        if our_rank is None:
            if OUR_NAME_MATCH in title.lower() or OUR_DOMAIN in domain.lower():
                our_rank = rank
    return {"our_rank": our_rank, "top3": top, "total_items": len(items)}


def cell_label(rank: int | None) -> str:
    if rank is None:
        return "  -"
    return f"{rank:>3}"


def render_ascii(points: list[dict[str, Any]], size: int) -> str:
    """Terminal grid. North at the top, business at the centre."""
    by_rc = {(p["row"], p["col"]): p for p in points}
    lines = []
    for row in range(size):
        cells = []
        for col in range(size):
            p = by_rc.get((row, col), {})
            r = p.get("our_rank")
            mark = "*" if p.get("is_home") else " "
            cells.append(f"{cell_label(r)}{mark}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def rank_colour(rank: int | None) -> str:
    if rank is None:
        return "#9aa0a6"          # not found
    if rank <= 3:
        return "#137333"          # in the 3-pack
    if rank <= 10:
        return "#b06000"          # page 1 of maps
    return "#c5221f"              # buried


def render_html(keyword: str, points: list[dict[str, Any]], size: int,
                spacing: float, stats: dict[str, Any]) -> str:
    by_rc = {(p["row"], p["col"]): p for p in points}
    cells = []
    for row in range(size):
        for col in range(size):
            p = by_rc.get((row, col), {})
            r = p.get("our_rank")
            colour = rank_colour(r)
            label = "–" if r is None else str(r)
            home = " home" if p.get("is_home") else ""
            title = f"{p.get('lat')}, {p.get('lng')}"
            top = p.get("top3") or []
            if top:
                title += " | " + "; ".join(f"#{t['rank']} {t['title']}" for t in top)
            cells.append(
                f'<div class="cell{home}" style="background:{colour}" title="{title}">{label}</div>'
            )
    grid = "\n".join(cells)
    span = round(spacing * (size - 1), 1)
    return f"""<!doctype html>
<meta charset="utf-8">
<title>Geo-grid — {keyword}</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 2rem; color: #202124; }}
  h1 {{ font-size: 1.25rem; margin-bottom: .25rem; }}
  .sub {{ color: #5f6368; font-size: .9rem; margin-bottom: 1.5rem; }}
  .grid {{ display: grid; grid-template-columns: repeat({size}, 56px); gap: 4px; }}
  .cell {{ height: 56px; display: flex; align-items: center; justify-content: center;
          color: #fff; font-weight: 600; border-radius: 6px; font-size: 1rem; }}
  .cell.home {{ outline: 3px solid #202124; outline-offset: 1px; }}
  .legend {{ margin-top: 1.5rem; font-size: .85rem; color: #5f6368; }}
  .key {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px;
          vertical-align: middle; margin: 0 4px 0 12px; }}
  table {{ border-collapse: collapse; margin-top: 1.5rem; font-size: .85rem; }}
  td, th {{ border-bottom: 1px solid #e0e0e0; padding: 4px 12px 4px 0; text-align: left; }}
</style>
<h1>Geo-grid rank map — “{keyword}”</h1>
<div class="sub">
  {size}×{size} grid, {spacing} miles apart ({span} × {span} miles), centred on SO18 1NQ.
  Number = Better Call Wes position on Google Maps at that point. Outlined cell = home.
</div>
<div class="grid">{grid}</div>
<div class="legend">
  <span class="key" style="background:#137333"></span> 3-pack (1–3)
  <span class="key" style="background:#b06000"></span> 4–10
  <span class="key" style="background:#c5221f"></span> 11+
  <span class="key" style="background:#9aa0a6"></span> not ranked
</div>
<table>
  <tr><th>Points searched</th><td>{stats['total']}</td></tr>
  <tr><th>In the 3-pack</th><td>{stats['in_pack']} ({stats['pct_pack']}%)</td></tr>
  <tr><th>Ranked anywhere</th><td>{stats['ranked']} ({stats['pct_ranked']}%)</td></tr>
  <tr><th>Not found</th><td>{stats['missing']}</td></tr>
  <tr><th>Average rank (where ranked)</th><td>{stats['avg_rank']}</td></tr>
</table>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--size", type=int, default=7, help="grid is size x size (default 7)")
    ap.add_argument("--spacing", type=float, default=1.5, help="miles between points")
    ap.add_argument("--date", default=None, help="snapshot stamp YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    grid = build_grid(args.size, args.spacing)
    est = len(grid) * COST_PER_POINT
    span = round(args.spacing * (args.size - 1), 1)
    print(f"keyword:  {args.keyword}")
    print(f"grid:     {args.size}x{args.size} = {len(grid)} points, "
          f"{args.spacing} mi apart ({span} x {span} mi)")
    print(f"centre:   {HOME_LAT}, {HOME_LNG}  (SO18 1NQ)")
    print(f"estimated cost: ${est:.4f}")
    if args.dry_run:
        print("\n(dry run — no API calls made)")
        return 0

    client = DataForSEOClient()
    half = args.size // 2
    for p in grid:
        p["is_home"] = (p["row"] == half and p["col"] == half)

    def run_point(p: dict[str, Any]) -> dict[str, Any]:
        try:
            return parse_point(fetch_point(client, args.keyword, p["lat"], p["lng"]))
        except DataForSEOError as e:
            return {"error": str(e)}

    print()
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_point, p): p for p in grid}
        for fut in as_completed(futures):
            p = futures[fut]
            p.update(fut.result())
            done += 1
            r = p.get("our_rank")
            state = f"#{r}" if r else ("ERR" if p.get("error") else "not ranked")
            print(f"  [{done:>2}/{len(grid)}] {p['lat']:.4f},{p['lng']:.4f}  "
                  f"{state} ({p.get('total_items', 0)} results)", flush=True)
    print(f"\nfetched {len(grid)} points in {time.time() - t0:.0f}s")

    ranks = [p["our_rank"] for p in grid if p.get("our_rank")]
    stats = {
        "total": len(grid),
        "ranked": len(ranks),
        "missing": len(grid) - len(ranks),
        "in_pack": sum(1 for r in ranks if r <= 3),
        "avg_rank": round(sum(ranks) / len(ranks), 1) if ranks else "n/a",
    }
    stats["pct_pack"] = round(100 * stats["in_pack"] / stats["total"])
    stats["pct_ranked"] = round(100 * stats["ranked"] / stats["total"])

    print("\n" + render_ascii(grid, args.size))
    print(f"\nin 3-pack: {stats['in_pack']}/{stats['total']} ({stats['pct_pack']}%)  |  "
          f"ranked: {stats['ranked']}/{stats['total']}  |  avg rank: {stats['avg_rank']}")

    slug = re.sub(r"[^a-z0-9]+", "-", args.keyword.lower()).strip("-")
    stamp = args.date or "latest"
    ddir = OUT_DATA / stamp
    ddir.mkdir(parents=True, exist_ok=True)
    (ddir / f"{slug}.json").write_text(json.dumps(
        {"keyword": args.keyword, "centre": [HOME_LAT, HOME_LNG], "size": args.size,
         "spacing_miles": args.spacing, "stats": stats, "points": grid}, indent=2))
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    html = OUT_REPORTS / f"geogrid-{stamp}-{slug}.html"
    html.write_text(render_html(args.keyword, grid, args.size, args.spacing, stats))
    print(f"\nData:   {ddir / f'{slug}.json'}")
    print(f"Visual: {html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
