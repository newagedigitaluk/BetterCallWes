"""
Social performance analyser for Better Call Wes.

Joins three data sources to answer "what actually works?":
  1. Zernio analytics  — impressions / likes / ER per published post
  2. content_bank.json — the pillar, image_type, image_hint, CTA of each post
  3. Linke (optional)  — per-post click counts

The join is what matters: Zernio alone tells you a post did well, but not
WHY. Joining to the bank's metadata tells you which *pillar* and *image
type* drive engagement — which is what we tune the next batch on.

Usage:
  ZERNIO_API_KEY=... python3 website/social/analyse_performance.py
  ... --days 90        # window (default 90)
  ... --json out.json  # dump the joined rows for further analysis
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

HERE = Path(__file__).parent
BANK_PATH = HERE / "content_bank.json"
BASE = "https://zernio.com/api/v1"

BCW_ACCOUNTS = {
    "69224444f43160a0bc998bc4": "facebook",
    "69224597f43160a0bc998bc8": "instagram",
    "693f5827f43160a0bc99b494": "googlebusiness",
}


def norm(s: str) -> str:
    """Normalise text for matching (strip emoji/punct/whitespace)."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())[:60]


def fetch_zernio(key: str) -> list:
    r = requests.get(f"{BASE}/analytics", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    r.raise_for_status()
    posts = r.json().get("posts", [])
    return [p for p in posts
            if any(pp.get("accountId") in BCW_ACCOUNTS for pp in p.get("platforms", []))]


def build_index(bank: dict) -> dict:
    """Map normalised opening text -> bank post, for every platform variant."""
    idx = {}
    for p in bank["posts"]:
        for field in ("facebook", "instagram", "googlebusiness", "twitter"):
            t = p.get(field)
            if t:
                k = norm(t)
                if k:
                    idx.setdefault(k, p)
    return idx


def join(zposts: list, idx: dict) -> tuple[list, int]:
    """Attach bank metadata to each Zernio post. Returns (rows, unmatched)."""
    rows, unmatched = [], 0
    for zp in zposts:
        k = norm(zp.get("content", ""))
        bp = idx.get(k)
        if not bp:
            # fall back to prefix match (content can be truncated/edited)
            for ik, ip in idx.items():
                if ik and (k.startswith(ik[:40]) or ik.startswith(k[:40])):
                    bp = ip
                    break
        if not bp:
            unmatched += 1
            continue
        a = zp.get("analytics") or {}
        plats = sorted({pp.get("platform") for pp in zp.get("platforms", [])
                        if pp.get("accountId") in BCW_ACCOUNTS})
        rows.append({
            "post_id": bp.get("id"),
            "pillar": bp.get("pillar"),
            "image_type": bp.get("image_type"),
            "image_hint": bp.get("image_hint", ""),
            "caption": bp.get("caption", ""),
            "topic": bp.get("topic", ""),
            "platform": plats[0] if plats else "?",
            "published": (zp.get("publishedAt") or "")[:10],
            "hour": (zp.get("publishedAt") or "")[11:13],
            "impressions": a.get("impressions") or 0,
            "reach": a.get("reach") or 0,
            "likes": a.get("likes") or 0,
            "comments": a.get("comments") or 0,
            "shares": a.get("shares") or 0,
            "saves": a.get("saves") or 0,
            "clicks": a.get("clicks") or 0,
            "er": a.get("engagementRate") or 0,
        })
    return rows, unmatched


def table(title, groups, key_label):
    """Print a sorted breakdown table."""
    print(f"\n{'='*78}\n{title}\n{'='*78}")
    print(f"  {key_label:<22} {'posts':>5} {'impr':>6} {'impr/post':>10} "
          f"{'likes':>6} {'eng':>5} {'eng/post':>9}")
    print("  " + "-" * 74)
    rank = sorted(groups.items(),
                  key=lambda kv: (kv[1]["eng"] / max(kv[1]["posts"], 1)), reverse=True)
    for k, d in rank:
        ipp = d["impr"] / max(d["posts"], 1)
        epp = d["eng"] / max(d["posts"], 1)
        print(f"  {str(k):<22} {d['posts']:>5} {d['impr']:>6} {ipp:>10.1f} "
              f"{d['likes']:>6} {d['eng']:>5} {epp:>9.2f}")
    return rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--json", type=str, default="")
    args = ap.parse_args()

    key = os.environ.get("ZERNIO_API_KEY", "")
    if not key:
        print("❌ ZERNIO_API_KEY not set"); sys.exit(1)

    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    zposts = fetch_zernio(key)
    idx = build_index(bank)
    rows, unmatched = join(zposts, idx)

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    rows = [r for r in rows
            if r["published"] and datetime.fromisoformat(r["published"] + "T00:00:00+00:00") >= since]

    print(f"📊 BCW social performance — last {args.days} days")
    print(f"   Zernio posts: {len(zposts)} | joined to bank: {len(rows)} | unmatched: {unmatched}")
    if not rows:
        print("   No joined rows — nothing to analyse."); return

    def blank():
        return {"posts": 0, "impr": 0, "likes": 0, "eng": 0}

    # engagement score weights shares/saves/comments above likes (discovery signals)
    def eng(r):
        return r["likes"] + 3 * r["comments"] + 5 * r["shares"] + 4 * r["saves"]

    by_pillar, by_itype, by_plat, by_hour = (defaultdict(blank) for _ in range(4))
    for r in rows:
        for grp, k in ((by_pillar, r["pillar"]), (by_itype, r["image_type"]),
                       (by_plat, r["platform"]), (by_hour, r["hour"] + ":00")):
            grp[k]["posts"] += 1
            grp[k]["impr"] += r["impressions"]
            grp[k]["likes"] += r["likes"]
            grp[k]["eng"] += eng(r)

    table("BY PILLAR (what topic type earns engagement)", by_pillar, "pillar")
    table("BY IMAGE TYPE (does showing Wes matter?)", by_itype, "image_type")
    table("BY PLATFORM", by_plat, "platform")
    table("BY POSTING HOUR", by_hour, "hour (UTC)")

    # Top / bottom individual posts
    ranked = sorted(rows, key=lambda r: (eng(r), r["impressions"]), reverse=True)
    print(f"\n{'='*78}\nTOP 10 POSTS\n{'='*78}")
    for r in ranked[:10]:
        print(f"  [{r['platform'][:2]}] {r['pillar'][:11]:11} eng={eng(r):>3} "
              f"impr={r['impressions']:>4} ❤{r['likes']:>2} 💬{r['comments']} ↻{r['shares']} "
              f"| {r['caption'][:40]}")
    print(f"\n{'='*78}\nBOTTOM 10 POSTS (zero-engagement)\n{'='*78}")
    for r in ranked[-10:]:
        print(f"  [{r['platform'][:2]}] {r['pillar'][:11]:11} eng={eng(r):>3} "
              f"impr={r['impressions']:>4} | {r['caption'][:40]}")

    totals = {
        "posts": len(rows),
        "impressions": sum(r["impressions"] for r in rows),
        "likes": sum(r["likes"] for r in rows),
        "comments": sum(r["comments"] for r in rows),
        "shares": sum(r["shares"] for r in rows),
        "saves": sum(r["saves"] for r in rows),
        "clicks": sum(r["clicks"] for r in rows),
    }
    print(f"\n{'='*78}\nTOTALS\n{'='*78}\n  {totals}")

    if args.json:
        json.dump(rows, open(args.json, "w"), indent=2)
        print(f"\n💾 Joined rows → {args.json}")


if __name__ == "__main__":
    main()
