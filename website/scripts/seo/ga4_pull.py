"""GA4 Data API pull — confirms engagement/landing-page story on a real sample.

Reuses the OAuth user token (analytics.readonly scope) from gsc-token.json.
Property id from .env (GA4_PROPERTY_ID).

Usage:
  python3 ga4_pull.py            # 28d + 90d reads
  python3 ga4_pull.py --days 90
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[3]
TOKEN = ROOT / ".credentials" / "gsc-token.json"
ENV = ROOT / ".env"


def prop_id() -> str:
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("GA4_PROPERTY_ID="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GA4_PROPERTY_ID not in .env")


def creds():
    d = json.loads(TOKEN.read_text())
    c = Credentials(token=d["token"], refresh_token=d["refresh_token"], token_uri=d["token_uri"],
                    client_id=d["client_id"], client_secret=d["client_secret"], scopes=d["scopes"])
    if not c.valid:
        c.refresh(Request())
        d["token"] = c.token
        TOKEN.write_text(json.dumps(d, indent=2))
    return c


def run(svc, pid, days, dims, mets, limit=15, order_metric=None):
    body = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": d} for d in dims],
        "metrics": [{"name": m} for m in mets],
        "limit": limit,
    }
    if order_metric:
        body["orderBys"] = [{"metric": {"metricName": order_metric}, "desc": True}]
    resp = svc.properties().runReport(property=f"properties/{pid}", body=body).execute()
    rows = []
    for r in resp.get("rows", []):
        dim_vals = [d["value"] for d in r.get("dimensionValues", [])]
        met_vals = [m["value"] for m in r.get("metricValues", [])]
        rows.append(dim_vals + met_vals)
    return rows


def show(title, dims, mets, rows):
    print(f"\n## {title}")
    if not rows:
        print("   (no data)")
        return
    header = dims + mets
    print("   " + " | ".join(header))
    for row in rows:
        print("   " + " | ".join(str(x) for x in row))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None)
    args = ap.parse_args()

    pid = prop_id()
    svc = build("analyticsdata", "v1beta", credentials=creds(), cache_discovery=False)
    windows = [args.days] if args.days else [28, 90]

    for days in windows:
        print("\n" + "=" * 64)
        print(f"GA4 property {pid} · last {days} days")
        print("=" * 64)

        show(f"Totals ({days}d)", ["—"], ["sessions", "engagedSessions", "engagementRate", "averageSessionDuration", "bounceRate", "screenPageViews"],
             run(svc, pid, days, [], ["sessions", "engagedSessions", "engagementRate", "averageSessionDuration", "bounceRate", "screenPageViews"]))

        show("By device", ["deviceCategory"], ["sessions", "engagementRate", "averageSessionDuration"],
             run(svc, pid, days, ["deviceCategory"], ["sessions", "engagementRate", "averageSessionDuration"], order_metric="sessions"))

        show("By channel", ["sessionDefaultChannelGroup"], ["sessions", "engagementRate", "averageSessionDuration"],
             run(svc, pid, days, ["sessionDefaultChannelGroup"], ["sessions", "engagementRate", "averageSessionDuration"], order_metric="sessions"))

        show("Top landing pages", ["landingPagePlusQueryString"], ["sessions", "engagementRate", "averageSessionDuration", "bounceRate"],
             run(svc, pid, days, ["landingPagePlusQueryString"], ["sessions", "engagementRate", "averageSessionDuration", "bounceRate"], order_metric="sessions"))

        show("Key events / conversions", ["eventName"], ["eventCount"],
             run(svc, pid, days, ["eventName"], ["eventCount"], order_metric="eventCount", limit=20))


if __name__ == "__main__":
    main()
