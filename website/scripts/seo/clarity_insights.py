"""Microsoft Clarity Data Export API client + reading.

Direct API approach (no MCP). Reads CLARITY_API_TOKEN from the repo .env.

API facts (https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-data-export-api):
  - Endpoint: GET https://www.clarity.ms/export-data/api/v1/project-live-insights
  - Auth: header  Authorization: Bearer <JWT token>
  - Params: numOfDays (1|2|3), dimension1, dimension2, dimension3
  - Dimensions: Browser, Device, Country, OS, Source, Medium, Campaign, Channel, URL
  - Window: last 1-3 days only
  - RATE LIMIT: 10 requests per project per DAY. Be frugal.

Token: Clarity project -> Settings -> Data export -> Generate new API token.

Usage:
  python3 clarity_insights.py                 # default reading: Device, URL, Source (3 calls)
  python3 clarity_insights.py --dims OS       # single custom call
  python3 clarity_insights.py --days 1 --dims URL Device   # one call, two dims
  python3 clarity_insights.py --raw           # dump raw JSON too

Snapshots saved to:
  ~/obsidian-vault/Better-Call-Wes/SEO-Data/clarity/YYYY-MM-DD/<dims>.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"
ENDPOINT = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
OUT_DIR = Path.home() / "obsidian-vault" / "Better-Call-Wes" / "SEO-Data" / "clarity"

VALID_DIMS = {"Browser", "Device", "Country", "OS", "Source", "Medium", "Campaign", "Channel", "URL"}


class ClarityError(Exception):
    pass


def load_token() -> str:
    if not ENV_PATH.exists():
        raise ClarityError(f"No .env at {ENV_PATH}")
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == "CLARITY_API_TOKEN":
            return v.strip().strip('"').strip("'")
    raise ClarityError("CLARITY_API_TOKEN not found in .env")


def fetch(token: str, num_days: int = 3, dims: list[str] | None = None) -> list[dict]:
    params = {"numOfDays": str(num_days)}
    for i, d in enumerate(dims or [], start=1):
        if d not in VALID_DIMS:
            raise ClarityError(f"Invalid dimension '{d}'. Valid: {sorted(VALID_DIMS)}")
        params[f"dimension{i}"] = d
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        if e.code == 401:
            raise ClarityError("401 Unauthorized — token invalid/expired. Regenerate in Clarity → Settings → Data export.")
        if e.code == 402 or e.code == 429:
            raise ClarityError(f"{e.code} — daily rate limit hit (10 requests/project/day). Try again tomorrow.")
        raise ClarityError(f"HTTP {e.code}: {body}")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def summarise(payload: list[dict]) -> None:
    """Print a compact reading. Clarity returns a list of metric blocks, each with
    'metricName' and 'information' (list of rows keyed by the requested dimensions)."""
    if not isinstance(payload, list):
        print(json.dumps(payload, indent=2)[:1000])
        return
    for block in payload:
        name = block.get("metricName", "?")
        info = block.get("information", [])
        print(f"\n## {name}  ({len(info)} row(s))")
        for row in info[:25]:
            # row is a dict of dim->value plus metric fields
            print("   " + "  ".join(f"{k}={row[k]}" for k in row))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3, choices=[1, 2, 3])
    ap.add_argument("--dims", nargs="*", default=None, help="1-3 dimensions for a single call")
    ap.add_argument("--raw", action="store_true", help="also print raw JSON")
    ap.add_argument("--date", default=None, help="snapshot folder date (YYYY-MM-DD); default skips disk write")
    args = ap.parse_args()

    token = load_token()

    # Default reading = 3 economical calls. Custom --dims = single call.
    calls = [args.dims] if args.dims is not None else [["Device"], ["URL"], ["Source"]]

    out_dir = (OUT_DIR / args.date) if args.date else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    for dims in calls:
        label = "-".join(dims) if dims else "overall"
        print("\n" + "=" * 60)
        print(f"CLARITY · last {args.days}d · dimension(s): {label}")
        print("=" * 60)
        data = fetch(token, args.days, dims)
        if out_dir:
            (out_dir / f"{label}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        summarise(data)
        if args.raw:
            print("\n--- raw ---")
            print(json.dumps(data, indent=2)[:4000])

    print("\n(Reqs used this run: %d of 10/day budget.)" % len(calls))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ClarityError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
