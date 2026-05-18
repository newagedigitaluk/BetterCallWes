"""Pull Google Search Console data and snapshot it to the obsidian vault.

Saves three flat JSONs per run:
  ~/obsidian-vault/Better-Call-Wes/SEO-Data/gsc/YYYY-MM-DD/pages.json
  ~/obsidian-vault/Better-Call-Wes/SEO-Data/gsc/YYYY-MM-DD/queries.json
  ~/obsidian-vault/Better-Call-Wes/SEO-Data/gsc/YYYY-MM-DD/queries-by-page.json

Default window: last 90 days. Override with --days N.

Usage:
    python3 website/scripts/seo/gsc_pull.py
    python3 website/scripts/seo/gsc_pull.py --days 28
    python3 website/scripts/seo/gsc_pull.py --page /services/boiler-repair.html
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from gsc_client import GSCClient, DEFAULT_PROPERTY

VAULT = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "gsc"
SITE_BASE = "https://bettercallwes.co.uk"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90, help="lookback window")
    parser.add_argument("--property", default=DEFAULT_PROPERTY)
    parser.add_argument(
        "--page",
        help="if set, also pull queries filtered to this page path "
        "(e.g. /services/boiler-repair.html)",
    )
    parser.add_argument(
        "--row-limit", type=int, default=2500, help="max rows per dimension cut"
    )
    args = parser.parse_args()

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=args.days)).isoformat()
    print(f"Window: {start} → {end} ({args.days} days)")

    c = GSCClient()
    out_dir = VAULT / end
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pages
    print("Pulling pages…")
    pages = c.search_analytics(
        site_url=args.property,
        start_date=start,
        end_date=end,
        dimensions=["page"],
        row_limit=args.row_limit,
    )
    pages.sort(key=lambda r: -r["impressions"])
    (out_dir / "pages.json").write_text(
        json.dumps({"start": start, "end": end, "rows": pages}, indent=2)
    )
    print(f"  {len(pages)} pages → {out_dir / 'pages.json'}")

    # Queries
    print("Pulling queries…")
    queries = c.search_analytics(
        site_url=args.property,
        start_date=start,
        end_date=end,
        dimensions=["query"],
        row_limit=args.row_limit,
    )
    queries.sort(key=lambda r: -r["impressions"])
    (out_dir / "queries.json").write_text(
        json.dumps({"start": start, "end": end, "rows": queries}, indent=2)
    )
    print(f"  {len(queries)} queries → {out_dir / 'queries.json'}")

    # Queries × Pages
    print("Pulling queries × pages…")
    cross = c.search_analytics(
        site_url=args.property,
        start_date=start,
        end_date=end,
        dimensions=["query", "page"],
        row_limit=args.row_limit,
    )
    cross.sort(key=lambda r: -r["impressions"])
    (out_dir / "queries-by-page.json").write_text(
        json.dumps({"start": start, "end": end, "rows": cross}, indent=2)
    )
    print(f"  {len(cross)} pairs → {out_dir / 'queries-by-page.json'}")

    # Optional: per-page filtered queries
    if args.page:
        page_url = args.page if args.page.startswith("http") else SITE_BASE + args.page
        print(f"Pulling queries for {page_url}…")
        page_q = c.search_analytics(
            site_url=args.property,
            start_date=start,
            end_date=end,
            dimensions=["query"],
            row_limit=args.row_limit,
            filters=[
                {"dimension": "page", "operator": "equals", "expression": page_url}
            ],
        )
        page_q.sort(key=lambda r: -r["impressions"])
        slug = args.page.strip("/").replace("/", "_").replace(".html", "") or "root"
        out_file = out_dir / f"queries-for-{slug}.json"
        out_file.write_text(
            json.dumps(
                {"start": start, "end": end, "page": page_url, "rows": page_q},
                indent=2,
            )
        )
        print(f"  {len(page_q)} queries → {out_file}")

    print(f"\nAll snapshots: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
