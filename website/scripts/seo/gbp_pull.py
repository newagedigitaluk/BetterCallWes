"""Google Business Profile snapshot + report.

Pulls the profile, reviews, performance metrics and local-posts summary into a
dated snapshot in the obsidian vault, and prints a readable report. Lets us
measure whether GBP changes (category, review replies, posts) move the map pack.

Reuses the OAuth user token (business.manage scope) from gsc-token.json.
ALWAYS force-refreshes the access token before calling — the GBP endpoints
reject a token cached from a previous process with a 401 even when it looks
valid, so creds.refresh() is mandatory, not conditional.

APIs used (all must be enabled on the bcw-seo Cloud project):
  - mybusinessbusinessinformation v1   (profile)
  - mybusiness v4 (legacy)             (reviews, localPosts)
  - businessprofileperformance v1      (calls / clicks / impressions)

Usage:
  python3 gbp_pull.py                 # snapshot last 90d perf + full reviews
  python3 gbp_pull.py --days 30
  python3 gbp_pull.py --no-save       # print only, don't write the snapshot

Snapshots: ~/obsidian-vault/Better-Call-Wes/SEO-Data/gbp/YYYY-MM-DD/
Report:    ~/obsidian-vault/Better-Call-Wes/SEO-Reports/gbp-YYYY-MM-DD.md
Pass --date YYYY-MM-DD to stamp the folder/report (the runtime forbids
auto-dating); otherwise files are written under 'latest/'.
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parents[3]
TOKEN = ROOT / ".credentials" / "gsc-token.json"
OUT_DATA = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "gbp"
OUT_REPORTS = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"

# Discovered via gbp_probe.py / account listing. Hard-coded so the script is
# self-contained; update if the location ever changes.
ACCOUNT = "accounts/103153500776465763190"
LOCATION_ID = "8703422495816802121"
LOCATION = f"locations/{LOCATION_ID}"

STAR = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
PERF_METRICS = [
    "CALL_CLICKS", "WEBSITE_CLICKS", "BUSINESS_DIRECTION_REQUESTS", "BUSINESS_CONVERSATIONS",
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH", "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS", "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
]


def token() -> str:
    d = json.loads(TOKEN.read_text())
    creds = Credentials(
        token=d["token"], refresh_token=d["refresh_token"], token_uri=d["token_uri"],
        client_id=d["client_id"], client_secret=d["client_secret"], scopes=d["scopes"],
    )
    creds.refresh(Request())  # mandatory — see module docstring
    d["token"] = creds.token
    TOKEN.write_text(json.dumps(d, indent=2))
    return creds.token


def api(tok: str, url: str):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]


def get_profile(tok):
    mask = "title,phoneNumbers,websiteUri,categories,serviceArea,regularHours,profile,openInfo,metadata"
    st, data = api(tok, f"https://mybusinessbusinessinformation.googleapis.com/v1/{LOCATION}?readMask={mask}")
    return data if st == 200 else {"_error": (st, data)}


def get_reviews(tok):
    revs, pt = [], None
    avg = total = None
    while True:
        url = f"https://mybusiness.googleapis.com/v4/{ACCOUNT}/{LOCATION}/reviews?pageSize=50" + (f"&pageToken={pt}" if pt else "")
        st, data = api(tok, url)
        if st != 200:
            return {"_error": (st, data)}
        avg = data.get("averageRating"); total = data.get("totalReviewCount")
        revs += data.get("reviews", [])
        pt = data.get("nextPageToken")
        if not pt:
            break
    return {"averageRating": avg, "totalReviewCount": total, "reviews": revs}


def get_posts(tok):
    posts, pt = [], None
    while True:
        url = f"https://mybusiness.googleapis.com/v4/{ACCOUNT}/{LOCATION}/localPosts?pageSize=100" + (f"&pageToken={pt}" if pt else "")
        st, data = api(tok, url)
        if st != 200:
            return {"_error": (st, data)}
        posts += data.get("localPosts", [])
        pt = data.get("nextPageToken")
        if not pt:
            break
    return {"posts": posts}


def get_performance(tok, start: date, end: date):
    base = f"https://businessprofileperformance.googleapis.com/v1/{LOCATION}:fetchMultiDailyMetricsTimeSeries"
    q = [
        ("dailyRange.startDate.year", start.year), ("dailyRange.startDate.month", start.month), ("dailyRange.startDate.day", start.day),
        ("dailyRange.endDate.year", end.year), ("dailyRange.endDate.month", end.month), ("dailyRange.endDate.day", end.day),
    ]
    for m in PERF_METRICS:
        q.append(("dailyMetrics", m))
    st, data = api(tok, base + "?" + urllib.parse.urlencode(q))
    if st != 200:
        return {"_error": (st, data)}
    out = {}
    for series in data.get("multiDailyMetricTimeSeries", []):
        for ts in series.get("dailyMetricTimeSeries", []):
            m = ts.get("dailyMetric")
            vals = ts.get("timeSeries", {}).get("datedValues", [])
            out[m] = sum(int(v.get("value", 0)) for v in vals if v.get("value"))
    return out


def build_report(profile, reviews, posts, perf, start, end) -> str:
    L = []
    L.append(f"# GBP report — {end.isoformat()}\n")
    L.append(f"- Performance window: **{start.isoformat()} → {end.isoformat()}**")
    cats = profile.get("categories", {})
    L.append(f"- Primary category: **{cats.get('primaryCategory', {}).get('displayName', '?')}**")
    L.append(f"- Additional: {', '.join(c.get('displayName','?') for c in cats.get('additionalCategories', []))}")
    L.append(f"- Phone: {profile.get('phoneNumbers', {}).get('primaryPhone', '?')}  •  Website: {profile.get('websiteUri','?')}")

    # Reviews
    revs = reviews.get("reviews", [])
    replied = sum(1 for r in revs if "reviewReply" in r)
    stars = Counter(STAR.get(r.get("starRating"), r.get("starRating")) for r in revs)
    recent90 = sum(1 for r in revs if r.get("createTime", "")[:10] >= (end - timedelta(days=90)).isoformat())
    L.append("\n## Reviews")
    L.append(f"- **{reviews.get('averageRating')}★** average over **{reviews.get('totalReviewCount')}** reviews")
    L.append(f"- Star breakdown: {dict(sorted(stars.items(), reverse=True))}")
    L.append(f"- Replied: **{replied}/{len(revs)}** ({len(revs)-replied} unanswered)")
    L.append(f"- New in last 90d: **{recent90}**")

    # Performance
    L.append("\n## Performance")
    if "_error" in perf:
        L.append(f"- (error: {perf['_error']})")
    else:
        impressions = sum(v for k, v in perf.items() if "IMPRESSIONS" in k)
        L.append(f"- Calls: **{perf.get('CALL_CLICKS',0)}**  •  Website clicks: **{perf.get('WEBSITE_CLICKS',0)}**  •  Directions: {perf.get('BUSINESS_DIRECTION_REQUESTS',0)}  •  Messages: {perf.get('BUSINESS_CONVERSATIONS',0)}")
        L.append(f"- **Total map/search impressions: {impressions}**")
        L.append(f"  - Search (desktop/mobile): {perf.get('BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',0)} / {perf.get('BUSINESS_IMPRESSIONS_MOBILE_SEARCH',0)}")
        L.append(f"  - Maps (desktop/mobile): {perf.get('BUSINESS_IMPRESSIONS_DESKTOP_MAPS',0)} / {perf.get('BUSINESS_IMPRESSIONS_MOBILE_MAPS',0)}")

    # Posts
    ps = posts.get("posts", [])
    L.append("\n## Local posts")
    if ps:
        ps_sorted = sorted(ps, key=lambda p: p.get("createTime", ""), reverse=True)
        recent30 = sum(1 for p in ps if p.get("createTime", "")[:10] >= (end - timedelta(days=30)).isoformat())
        L.append(f"- Total live posts: **{len(ps)}**  •  in last 30d: **{recent30}**")
        L.append(f"- Newest: {ps_sorted[0].get('createTime','')[:10]}  •  Oldest: {ps_sorted[-1].get('createTime','')[:10]}")
    else:
        L.append("- (none found via API)")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--date", default=None, help="snapshot date stamp YYYY-MM-DD (runtime can't auto-date)")
    args = ap.parse_args()

    tok = token()

    # Window: caller supplies the end date via --date (GBP perf lags ~2-3 days
    # anyway). Without it we use a relative span the API still accepts.
    end = date.fromisoformat(args.date) if args.date else None
    if end is None:
        # No date provided: ask the API for a fixed historical span we know works.
        # Use a wide window ending "recently"; the perf API clamps to available data.
        end = date(2026, 1, 1)  # placeholder; overwritten below if --date given
        # Without a real "today" we can't compute a live window, so require --date for perf.
        print("NOTE: no --date supplied; pulling profile/reviews/posts only. "
              "Pass --date YYYY-MM-DD for the performance window.\n")
        perf = {"_error": "no --date; perf window skipped"}
        start = end
    else:
        start = end - timedelta(days=args.days)

    profile = get_profile(tok)
    reviews = get_reviews(tok)
    posts = get_posts(tok)
    perf = get_performance(tok, start, end) if args.date else perf

    report = build_report(profile, reviews, posts, perf, start, end)
    print(report)

    if not args.no_save:
        stamp = args.date or "latest"
        ddir = OUT_DATA / stamp
        ddir.mkdir(parents=True, exist_ok=True)
        (ddir / "profile.json").write_text(json.dumps(profile, indent=2))
        (ddir / "reviews.json").write_text(json.dumps(reviews, indent=2))
        (ddir / "performance.json").write_text(json.dumps(perf, indent=2))
        (ddir / "posts_summary.json").write_text(json.dumps(
            {"count": len(posts.get("posts", [])),
             "newest": max((p.get("createTime", "") for p in posts.get("posts", [])), default=None)}, indent=2))
        OUT_REPORTS.mkdir(parents=True, exist_ok=True)
        (OUT_REPORTS / f"gbp-{stamp}.md").write_text(report)
        print(f"\nSnapshot: {ddir}")
        print(f"Report:   {OUT_REPORTS / f'gbp-{stamp}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
