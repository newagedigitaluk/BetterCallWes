"""Pull low-star Google reviews for top Southampton plumbing/heating firms.

Steps:
  1. Search Google Business Data for plumbing/heating queries to get the top
     listed businesses.
  2. For each unique business, pull reviews filtered to 1-3 stars.
  3. Write raw JSON to SEO-Data/competitor-reviews/YYYY-MM-DD/
  4. Write a summary report to SEO-Reports/competitor-reviews-YYYY-MM-DD.md

DataForSEO endpoints used:
  POST /v3/business_data/google/search/live
  POST /v3/business_data/google/reviews/live

Usage:
  python3 website/scripts/competitor_reviews.py
  python3 website/scripts/competitor_reviews.py --dry-run
  python3 website/scripts/competitor_reviews.py --max-reviews 50
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

# Point at the live project's seo/ folder for the DataForSEO client
SEO_SCRIPTS = Path("/home/wes/Coding/Projects/Better Call Wes/website/scripts/seo")
sys.path.insert(0, str(SEO_SCRIPTS))
from dataforseo_client import DataForSEOClient, DataForSEOError  # noqa: E402

LOCATION_CODE = 1006886  # Southampton, UK
LANGUAGE_CODE = "en"
OUR_BUSINESS = "Better Call Wes"

SEARCH_QUERIES = [
    "plumber Southampton",
    "heating engineer Southampton",
    "boiler repair Southampton",
    "emergency plumber Southampton",
    "gas engineer Southampton",
]

DATA_DIR = (
    Path.home()
    / "obsidian-vault"
    / "Better-Call-Wes"
    / "SEO-Data"
    / "competitor-reviews"
)
REPORT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Reports"


def search_businesses(
    client: DataForSEOClient, query: str
) -> tuple[list[dict[str, Any]], float]:
    payload = [
        {
            "keyword": query,
            "location_code": LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
            "depth": 10,
        }
    ]
    raw = client.post("/v3/business_data/google/search/live", payload)
    cost = float(raw.get("cost") or 0)
    items: list[dict[str, Any]] = []
    for task in raw.get("tasks") or []:
        sc = task.get("status_code")
        if sc != 20000:
            print(f"  search task error {sc}: {task.get('status_message')}", file=sys.stderr)
            continue
        for result in task.get("result") or []:
            for item in result.get("items") or []:
                # Different result types depending on API version
                itype = item.get("type", "")
                if itype in ("maps_search",):
                    for place in item.get("items") or []:
                        items.append(place)
                elif itype in ("local_pack",):
                    for place in item.get("items") or []:
                        items.append(place)
                else:
                    items.append(item)
    return items, cost


def fetch_reviews(
    client: DataForSEOClient, place_id: str, depth: int = 50
) -> tuple[list[dict[str, Any]], float]:
    payload = [
        {
            "place_id": place_id,
            "location_code": LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
            "depth": depth,
            "sort_by": "newest",
        }
    ]
    raw = client.post("/v3/business_data/google/reviews/live", payload)
    cost = float(raw.get("cost") or 0)
    reviews: list[dict[str, Any]] = []
    for task in raw.get("tasks") or []:
        sc = task.get("status_code")
        if sc != 20000:
            print(f"  reviews task error {sc}: {task.get('status_message')}", file=sys.stderr)
            continue
        for result in task.get("result") or []:
            for item in result.get("items") or []:
                reviews.append(item)
    return reviews, cost


def low_star(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in reviews:
        rating = r.get("rating")
        if isinstance(rating, dict):
            val = rating.get("value", 5)
        elif isinstance(rating, (int, float)):
            val = rating
        else:
            val = 5
        if val <= 3:
            out.append(r)
    return out


def categorise(text: str) -> list[str]:
    """Tag review text with complaint categories."""
    t = text.lower()
    tags: list[str] = []

    if any(w in t for w in [
        "didn't show", "did not show", "no show", "never turned up",
        "never came", "never arrived", "stood up", "no one came",
        "no one showed", "not turn up", "failed to show", "ghosted",
    ]):
        tags.append("no-show")

    if any(w in t for w in [
        "no call", "no update", "no response", "not respond",
        "didn't call", "did not call", "hard to reach", "couldn't get hold",
        "could not get hold", "no reply", "not reply", "ignored",
        "didn't get back", "did not get back", "communication",
        "not contact", "didn't contact", "radio silence",
    ]):
        tags.append("poor-communication")

    if any(w in t for w in [
        "overcharged", "over charged", "unexpected charge", "extra charge",
        "hidden fee", "hidden cost", "more than quoted", "higher than quoted",
        "price change", "changed the price", "added on", "extortionate",
        "rip off", "rip-off", "ripoff", "overpriced",
        "shocking price", "surprised by the price", "not what i was quoted",
    ]):
        tags.append("surprise-pricing")

    if any(w in t for w in [
        "left a mess", "left mess", "dirty", "mess behind",
        "did not clean", "didn't clean", "rubbish left", "debris",
        "muddy", "footprints", "muck",
    ]):
        tags.append("mess")

    if any(w in t for w in [
        "still leaking", "still broken", "not fixed", "came back",
        "bodge", "poor quality", "bad job", "wrong part",
        "made it worse", "made worse", "fault",
        "returned", "call back", "callback",
    ]):
        tags.append("quality-rework")

    if any(w in t for w in [
        "late", "hours late", "delayed", "long time",
        "wait", "took ages", "took forever", "weeks to", "months to",
    ]):
        tags.append("lateness")

    if any(w in t for w in [
        "rude", "arrogant", "dismissive", "unprofessional",
        "aggressive", "attitude",
    ]):
        tags.append("rudeness")

    return tags or ["other"]


def rating_val(r: dict[str, Any]) -> float:
    rating = r.get("rating")
    if isinstance(rating, dict):
        return float(rating.get("value", 5))
    if isinstance(rating, (int, float)):
        return float(rating)
    return 5.0


def build_angles(tag_counter: Counter) -> list[dict[str, str]]:
    angles = []

    if tag_counter.get("no-show", 0) > 0:
        angles.append({
            "title": "Show up. Every time.",
            "pain": "Customers book a plumber, take time off work, and nobody arrives.",
            "reel_hook": (
                "POV: you booked a plumber, cleared your diary, and they just "
                "did not show. Here is what I do instead."
            ),
            "ad_headline": "Booked. Confirmed. Here on time.",
            "caption": (
                "I know how frustrating it is to wait in all day and get stood up. "
                "That is why I always confirm the morning of and show up when I say I will. "
                "WhatsApp me and book a slot that works for you."
            ),
        })

    if tag_counter.get("poor-communication", 0) > 0:
        angles.append({
            "title": "You will always know what is happening.",
            "pain": "Customers are left in the dark while their plumber goes quiet.",
            "reel_hook": (
                "Still waiting to hear back from your plumber? "
                "I reply to every message, same day."
            ),
            "ad_headline": "Message me on WhatsApp. I actually reply.",
            "caption": (
                "One of the most common complaints about tradespeople? "
                "Total radio silence. I keep you updated at every step: "
                "when I am on my way, what I found, what it costs, when it is done."
            ),
        })

    if tag_counter.get("surprise-pricing", 0) > 0:
        angles.append({
            "title": "No surprises on the invoice.",
            "pain": "Customers get a low quote then a much higher final bill.",
            "reel_hook": (
                "What your plumber quoted vs what they charged. "
                "Here is how I do pricing."
            ),
            "ad_headline": "Price agreed before I start. No extras added after.",
            "caption": (
                "I give you a price before I pick up a tool. "
                "If the job changes, I tell you first and we agree before I carry on. "
                "No nasty surprises when the invoice lands."
            ),
        })

    if tag_counter.get("mess", 0) > 0:
        angles.append({
            "title": "I leave your home as I found it.",
            "pain": "Customers are left cleaning up after the tradesperson.",
            "reel_hook": (
                "Before I go: dust sheets down, tools picked up, rubbish bagged. "
                "Here is my end-of-job routine."
            ),
            "ad_headline": "Job done. Home clean. That is the standard.",
            "caption": (
                "Overshoes on, dust sheets down, waste bagged before I leave. "
                "Your home should look better after I visit, not worse."
            ),
        })

    if tag_counter.get("quality-rework", 0) > 0:
        angles.append({
            "title": "Fixed properly, first time.",
            "pain": "Customers have the same fault return days after a repair.",
            "reel_hook": (
                "Still the same problem? Here is why some repairs do not last "
                "and what I do differently."
            ),
            "ad_headline": "Gas Safe. Done right. No call-backs.",
            "caption": (
                "Gas Safe registered, fully insured, and I diagnose the root cause "
                "rather than patch over the symptom. "
                "If a fault returns within 30 days I will come back at no charge."
            ),
        })

    if tag_counter.get("lateness", 0) > 0:
        angles.append({
            "title": "On time, or I will let you know.",
            "pain": "Customers wait hours past the agreed arrival window.",
            "reel_hook": "Running late? I will tell you before you even have to ask.",
            "ad_headline": "Arrival window agreed. I stick to it.",
            "caption": (
                "I give you an arrival window and I stick to it. "
                "If something changes on the road I message you straight away. "
                "Your time matters."
            ),
        })

    # Trust anchor -- always include
    angles.append({
        "title": "Gas Safe. Fully insured. Sole trader.",
        "pain": "Customers are not sure if the person showing up is qualified.",
        "reel_hook": (
            "Before you let any gas engineer into your home, check these three things."
        ),
        "ad_headline": "Gas Safe registered. Fully insured. 5-star rated in Southampton.",
        "caption": (
            "I am Wes: Gas Safe registered, fully insured, and I work alone "
            "so you always know who is coming through your door. "
            "No subcontractors, no call-centre, just me."
        ),
    })

    return angles


def build_report(
    date_str: str,
    businesses: list[dict[str, Any]],
    all_low: list[dict[str, Any]],
    total_cost: float,
) -> str:
    tag_counter: Counter[str] = Counter()
    for r in all_low:
        for tag in r.get("tags", []):
            tag_counter[tag] += 1

    lines = [
        "# Competitor complaints analysis -- Southampton plumbing and heating",
        f"# {date_str}",
        "",
        (
            f"Pulled {len(all_low)} low-star reviews (1-3 stars) across "
            f"{len(businesses)} competitors. API cost: ${total_cost:.4f}."
        ),
        "",
        "---",
        "",
        "## Businesses surveyed",
        "",
    ]

    for b in businesses:
        rating = b.get("rating", {})
        if isinstance(rating, dict):
            avg = rating.get("value")
        else:
            avg = rating
        count = b.get("reviews_count") or b.get("rating_count") or "?"
        low_count = b.get("low_star_count", 0)
        name = b.get("title") or b.get("name") or "Unknown"
        lines.append(
            f"- **{name}** -- avg {avg}/5 ({count} reviews total, "
            f"{low_count} at 1-3 stars)"
        )

    lines += [
        "",
        "---",
        "",
        "## Complaint theme totals",
        "",
        "| Theme | Reviews |",
        "|---|---:|",
    ]
    for tag, count in tag_counter.most_common():
        lines.append(f"| {tag} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## Sample complaints by theme",
        "",
    ]

    for tag, _ in tag_counter.most_common():
        matching = [r for r in all_low if tag in r.get("tags", [])][:5]
        if not matching:
            continue
        lines.append(f"### {tag}")
        lines.append("")
        for r in matching:
            stars = rating_val(r)
            text = (r.get("review_text") or "").replace("\n", " ").strip()[:300]
            biz = r.get("business_name", "")
            lines.append(f"- **{stars:.0f} stars** ({biz}): {text}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Content angles for BCW reels and ads",
        "",
        "Rules: never name a competitor. Focus on what BCW does.",
        "",
    ]

    for a in build_angles(tag_counter):
        lines.append(f"### {a['title']}")
        lines.append("")
        lines.append(f"**Pain addressed**: {a['pain']}")
        lines.append("")
        lines.append(f"**Reel hook**: {a['reel_hook']}")
        lines.append("")
        lines.append(f"**Ad headline**: {a['ad_headline']}")
        lines.append("")
        lines.append(f"**Caption angle**: {a['caption']}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-reviews", type=int, default=100,
        help="max reviews to fetch per business (default 100)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = date.today().isoformat()

    if args.dry_run:
        print("dry run: would search these queries:")
        for q in SEARCH_QUERIES:
            print(f"  - {q}")
        est = len(SEARCH_QUERIES) * 0.004 + 10 * 0.0015
        print(f"estimated API cost: ~${est:.4f}")
        return 0

    client = DataForSEOClient()
    total_cost = 0.0

    # Step 1: collect unique businesses
    seen: set[str] = set()
    businesses: list[dict[str, Any]] = []

    print("[reviews] searching for Southampton plumbing businesses...")
    for query in SEARCH_QUERIES:
        print(f"  query: {query}")
        try:
            items, cost = search_businesses(client, query)
        except DataForSEOError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue
        total_cost += cost
        for item in items:
            pid = item.get("place_id") or item.get("cid")
            if not pid:
                continue
            name = item.get("title") or item.get("name") or ""
            if OUR_BUSINESS.lower() in name.lower():
                continue
            if pid not in seen:
                seen.add(pid)
                businesses.append(item)
        print(f"    {len(items)} results, cost ${cost:.4f}, unique so far: {len(businesses)}")

    if not businesses:
        print("No businesses found -- check API credentials or location code.", file=sys.stderr)
        # Save what we have so the run is not wasted
        out_path = DATA_DIR / today
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "search_failed.json").write_text(
            json.dumps({"error": "no businesses returned"}, indent=2), encoding="utf-8"
        )
        return 1

    # Limit to 10
    businesses = businesses[:10]
    print(f"\n[reviews] fetching low-star reviews for {len(businesses)} businesses...")

    out_dir = DATA_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)

    all_low: list[dict[str, Any]] = []

    for biz in businesses:
        pid = biz.get("place_id") or biz.get("cid") or ""
        name = biz.get("title") or biz.get("name") or pid
        print(f"  {name}  (place_id: {pid})")
        try:
            reviews, cost = fetch_reviews(client, pid, depth=args.max_reviews)
        except DataForSEOError as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            biz["low_star_count"] = 0
            continue
        total_cost += cost
        low = low_star(reviews)
        for r in low:
            r["tags"] = categorise(r.get("review_text") or "")
            r["business_name"] = name
        biz["low_star_count"] = len(low)
        all_low.extend(low)
        print(f"    {len(reviews)} reviews, {len(low)} at 1-3 stars, cost ${cost:.4f}")

        (out_dir / f"{pid}.json").write_text(
            json.dumps({"place_id": pid, "name": name, "reviews": reviews, "low_star": low}, indent=2),
            encoding="utf-8",
        )

    print(f"\n[reviews] total API cost: ${total_cost:.4f}")
    print(f"[reviews] low-star reviews collected: {len(all_low)}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"competitor-reviews-{today}.md"
    report_text = build_report(today, businesses, all_low, total_cost)
    report_path.write_text(report_text, encoding="utf-8")
    print(f"[reviews] report written: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
