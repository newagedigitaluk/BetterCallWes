"""GMB Briefcase API client — GBP management across multiple client listings.

White-label agency tier: up to 50 listings. This wraps the endpoints we actually
care about; the full collection is documented at
https://documenter.getpostman.com/view/6809322/2sBXwwonvE

Credentials live in the project .env (never commit them):
    GMB_BRIEFCASE_URL=https://<your-instance>      # 'api_url' in your account
    GMB_BRIEFCASE_KEY=<your api key>               # account settings

Auth is `Authorization: Bearer <key>` on every call.

Usage:
    python3 gmb_briefcase.py listings
    python3 gmb_briefcase.py insights --listing 12345 --days 90
    python3 gmb_briefcase.py keywords --listing 12345
    python3 gmb_briefcase.py reviews --listing 12345
    python3 gmb_briefcase.py geogrid --listing 12345 \
        --keyword "boiler repair southampton" --grid 7 --distance 1500

Notes:
  - Rate limits are per subscription plan; the client retries 429/5xx.
  - geogrid kicks off a report server-side. Treat it as a job, not a live read.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 90
MAX_RETRIES = 4
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


class GMBBriefcaseError(Exception):
    pass


class GMBBriefcaseClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 timeout: int = DEFAULT_TIMEOUT) -> None:
        env = _load_env(_project_root() / ".env")
        base_url = base_url or env.get("GMB_BRIEFCASE_URL") or os.environ.get("GMB_BRIEFCASE_URL")
        api_key = api_key or env.get("GMB_BRIEFCASE_KEY") or os.environ.get("GMB_BRIEFCASE_KEY")
        if not base_url or not api_key:
            raise GMBBriefcaseError(
                "Missing GMB_BRIEFCASE_URL / GMB_BRIEFCASE_KEY.\n"
                "Add them to the project .env:\n"
                "  GMB_BRIEFCASE_URL=https://<your-instance>\n"
                "  GMB_BRIEFCASE_KEY=<your api key>"
            )
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._timeout = timeout

    # -- transport ---------------------------------------------------------
    def _request(self, method: str, path: str, *, params: dict | None = None,
                 body: dict | None = None) -> dict[str, Any]:
        url = self._base + (path if path.startswith("/") else "/" + path)
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self._key}", "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"

        last: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as r:
                    payload = json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                last = e
                if e.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                    self._sleep(attempt)
                    continue
                detail = e.read().decode("utf-8", "replace")[:400]
                raise GMBBriefcaseError(f"HTTP {e.code} {e.reason}: {detail}") from e
            except urllib.error.URLError as e:
                last = e
                if attempt < MAX_RETRIES:
                    self._sleep(attempt)
                    continue
                raise GMBBriefcaseError(f"Network error: {e}") from e
            code = payload.get("code")
            if code is not None and int(code) >= 400:
                raise GMBBriefcaseError(f"API {code}: {payload.get('message')}")
            return payload
        raise GMBBriefcaseError(f"Exhausted retries: {last}")

    def get(self, path: str, **params) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict) -> dict[str, Any]:
        return self._request("POST", path, body=body)

    # -- endpoints we use --------------------------------------------------
    def listings(self) -> list[dict[str, Any]]:
        d = self.get("/api/v1/user/get-listings").get("data") or {}
        return d.get("locationLists") or []

    def insights(self, listing_id: str | int, days: int = 30) -> dict[str, Any]:
        return self.get("/api/v1/user/get-insights-summary",
                        listingId=listing_id, dateRange=days).get("data") or {}

    def customer_actions(self, listing_id: str | int, days: int = 30) -> dict[str, Any]:
        return self.get("/api/v1/user/get-customer-actions",
                        listingId=listing_id, dateRange=days).get("data") or {}

    def top_keywords(self, listing_id: str | int, month: str | None = None) -> dict[str, Any]:
        return self.get("/api/v1/user/get-top-keyword-query",
                        listingId=listing_id, month=month).get("data") or {}

    def review_summary(self, listing_id: str | int) -> dict[str, Any]:
        return self.get("/api/v1/user/get-review-summary",
                        listingId=listing_id).get("data") or {}

    def geo_ranking(self, listing_id: str | int, keyword: str, *, grid_size: int = 7,
                    distance: int = 1500, language: str = "en",
                    engine: str = "Map API", schedule: str = "onetime") -> dict[str, Any]:
        """Kick off a geo-grid report. distance units follow the dashboard's
        setting — confirm against a known run before trusting the scale."""
        return self.post("/api/v1/user/generate-geo-ranking-report", {
            "listingId": listing_id,
            "language": language,
            "keywords": keyword,
            "mapPoint": "Automatic",
            "distanceValue": distance,
            "gridSize": grid_size,
            "searchDataEngine": engine,
            "scheduleCheck": schedule,
        })


def main() -> int:
    ap = argparse.ArgumentParser(description="GMB Briefcase API")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("listings", help="list all connected GBP listings")

    p = sub.add_parser("insights"); p.add_argument("--listing", required=True); p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("actions"); p.add_argument("--listing", required=True); p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("keywords"); p.add_argument("--listing", required=True); p.add_argument("--month")
    p = sub.add_parser("reviews"); p.add_argument("--listing", required=True)
    p = sub.add_parser("geogrid")
    p.add_argument("--listing", required=True)
    p.add_argument("--keyword", required=True)
    p.add_argument("--grid", type=int, default=7)
    p.add_argument("--distance", type=int, default=1500)
    p.add_argument("--schedule", default="onetime")

    args = ap.parse_args()
    c = GMBBriefcaseClient()

    if args.cmd == "listings":
        rows = c.listings()
        print(f"{len(rows)} listing(s) connected (tier cap: 50)\n")
        for r in rows:
            print(f"  id={r.get('id'):<10} {r.get('locationName')}")
            print(f"  {'':<13} {r.get('city')}, {r.get('state')} {r.get('zipCode')}  |  {r.get('latlong')}")
        return 0

    if args.cmd == "insights":
        d = c.insights(args.listing, args.days)
        tf = d.get("timeframe", {})
        print(f"window: {tf.get('start_date')} -> {tf.get('end_date')} "
              f"(vs {tf.get('previous_start_date')} -> {tf.get('previous_end_date')})\n")
        for section in ("visibility_summary", "customer_actions"):
            if section not in d:
                continue
            print(section.replace("_", " ").upper())
            for k, v in d[section].items():
                if isinstance(v, dict):
                    cur = v.get("current_period", v.get("value"))
                    chg = v.get("percentage_change", v.get("change_percentage"))
                    trend = v.get("trend", "")
                    print(f"  {k:<24} {cur}   ({chg}% {trend})".rstrip())
                else:
                    print(f"  {k:<24} {v}")
            print()
        return 0

    if args.cmd == "actions":
        d = c.customer_actions(args.listing, args.days)
        for k, v in (d.get("actions_breakdown") or {}).items():
            print(f"  {k:<20} total={v.get('total'):<6} avg/day={v.get('daily_average'):<6} "
                  f"peak={v.get('peak_value')} on {v.get('peak_day') or '-'}")
        return 0

    if args.cmd == "keywords":
        d = c.top_keywords(args.listing, args.month)
        print(f"{d.get('MonthName')}\n")
        for row in (d.get("Monthdata") or []):
            print(f"  {int(row.get('impressions',0)):>6}  {row.get('keyword')}")
        return 0

    if args.cmd == "reviews":
        print(json.dumps(c.review_summary(args.listing), indent=2))
        return 0

    if args.cmd == "geogrid":
        r = c.geo_ranking(args.listing, args.keyword, grid_size=args.grid,
                          distance=args.distance, schedule=args.schedule)
        print(json.dumps(r, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
