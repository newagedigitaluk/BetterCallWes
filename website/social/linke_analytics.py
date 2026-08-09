"""
Pull click analytics for Better Call Wes Linke short links and produce a
leaderboard joined to post topics + pillars.

Usage:
    LINKE_API_KEY=... python3 website/social/linke_analytics.py [--limit N]

Output:
- Account totals + top N posts by clicks
- Pillar-level click summary (which content type drives the most clicks)
- Recent activity (posts sent in last N days)

Rate limit safe: 1 Linke call per post + 1 for account info. With ~90 posts
this uses ~91 requests of the 500/day quota.
"""
import json
import sys
import time
import argparse
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
BANK_PATH = PROJECT_ROOT / "website" / "social" / "content_bank.json"

sys.path.insert(0, str(PROJECT_ROOT / "website" / "social"))
from linke_client import LinkeClient


def fetch_clicks_via_list(client: LinkeClient, folder: str = "Better Call Wes") -> dict:
    """
    Fetch click counts for the whole folder in one paginated sweep — much
    cheaper than calling /view per link. Returns {short_link_url: total_hits}.
    """
    by_url = {}
    page = 1
    while True:
        links = client.list_short_links(folder=folder, page=page)
        if not links:
            break
        for link in links:
            try:
                hits = int(link.get("total_hits") or 0)
            except (TypeError, ValueError):
                hits = 0
            by_url[link.get("short_link")] = {
                "hits": hits,
                "original": link.get("original_link"),
                "title": link.get("title"),
                "created": link.get("creation_time"),
            }
        if len(links) < 50:
            break
        page += 1
        time.sleep(0.3)
    return by_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15,
                        help="Top N posts to show (default 15)")
    args = parser.parse_args()

    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    posts = bank.get("posts", [])

    # Build a map of short_link → post for quick join
    posts_by_url = {p.get("short_link"): p for p in posts if p.get("short_link")}

    print(f"📊 Posts with tracking links: {len(posts_by_url)}")
    if not posts_by_url:
        print("⚠️  No posts have short_link populated yet. Run create_post_links.py first.")
        return

    client = LinkeClient()

    # Account-level
    info = client.account_info()
    print(f"\n📈 Linke account: {info.get('email')} ({info.get('status')})")
    print(f"   Total links across all folders: {info.get('short_links')}")
    print(f"   Total clicks across all folders: {info.get('total_hits')}")

    print(f"\n🔄 Fetching click counts from 'Better Call Wes' folder...")
    folder_data = fetch_clicks_via_list(client)
    print(f"   Retrieved data for {len(folder_data)} folder links")

    # Join clicks back to posts
    rows = []
    for url, post in posts_by_url.items():
        data = folder_data.get(url, {})
        rows.append({
            "post_id":   post.get("id", "?"),
            "pillar":    post.get("pillar", "?"),
            "topic":     (post.get("topic") or "")[:55],
            "short":     url.replace("https://u.bettercallwes.co.uk/", "u.bcw.co.uk/"),
            "hits":      data.get("hits", 0),
            "sent_at":   (post.get("sent_at") or "—")[:10],
            "status":    post.get("status", "pending"),
        })

    # Leaderboard
    rows.sort(key=lambda r: r["hits"], reverse=True)

    print(f"\n🏆 TOP {args.limit} POSTS BY CLICKS")
    print("=" * 102)
    print(f"  {'#':>2}  {'POST':>9}  {'PILLAR':<14}  {'CLICKS':>6}  {'STATUS':<9}  {'SENT':<11}  TOPIC")
    print("-" * 102)
    for i, r in enumerate(rows[:args.limit], 1):
        print(f"  {i:>2}  {r['post_id']:>9}  {r['pillar']:<14}  {r['hits']:>6}  {r['status']:<9}  {r['sent_at']:<11}  {r['topic']}")
    print("=" * 102)

    # Pillar-level summary
    by_pillar = defaultdict(lambda: {"clicks": 0, "posts": 0, "sent": 0})
    for r in rows:
        p = by_pillar[r["pillar"]]
        p["clicks"] += r["hits"]
        p["posts"] += 1
        if r["status"] == "sent":
            p["sent"] += 1

    print(f"\n📊 CLICKS BY PILLAR")
    print("-" * 60)
    print(f"  {'PILLAR':<16}  {'POSTS':>6}  {'SENT':>5}  {'CLICKS':>7}  {'CLICKS/SENT':>11}")
    print("-" * 60)
    for pillar, d in sorted(by_pillar.items(), key=lambda kv: kv[1]["clicks"], reverse=True):
        per_sent = d["clicks"] / d["sent"] if d["sent"] else 0
        print(f"  {pillar:<16}  {d['posts']:>6}  {d['sent']:>5}  {d['clicks']:>7}  {per_sent:>11.2f}")
    print("-" * 60)

    total_clicks = sum(r["hits"] for r in rows)
    print(f"\n  TOTAL CLICKS (this folder, this set of posts): {total_clicks}")


if __name__ == "__main__":
    main()
