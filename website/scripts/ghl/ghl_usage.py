"""Count billable HighLevel traffic on the BCW sub-account, per month.

Read-only. Pages through the conversations message export for each channel and
prints a markdown table: messages in/out, SMS segments out, call minutes in/out
(rounded up per call, as carriers bill). Paste the output into the cost log in
docs/GHL-SETUP.md.

    with-secret .env -- python3 website/scripts/ghl/ghl_usage.py 2026-10-01 [2026-11-01]
"""
import collections
import math
import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ghl_api import call  # noqa: E402

CHANNELS = ["SMS", "Email", "Call", "WhatsApp"]
GSM = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡"
          "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà^{}\\[~]|€")


def segments(body):
    body = body or ""
    if all(ch in GSM for ch in body):
        return 1 if len(body) <= 160 else math.ceil(len(body) / 153)
    return 1 if len(body) <= 70 else math.ceil(len(body) / 67)


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-10-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "9999"
    rows = collections.defaultdict(collections.Counter)
    for ch in CHANNELS:
        cursor, pages = None, 0
        while pages < 200:
            path = f"/conversations/messages/export?locationId={{LOC}}&limit=100&channel={ch}"
            if cursor:
                path += "&cursor=" + quote(cursor)
            st, js = call("GET", path)
            if st != 200:
                print(f"<!-- {ch}: HTTP {st} {str(js)[:120]} -->")
                break
            msgs = js.get("messages", [])
            stop = False
            for m in msgs:
                d = (m.get("dateAdded") or "")[:10]
                if d < start:
                    stop = True
                    continue
                if d >= end:
                    continue
                k = rows[(d[:7], ch)]
                k[m.get("direction") or "none"] += 1
                if ch == "SMS" and m.get("direction") == "outbound":
                    k["segments_out"] += segments(m.get("body"))
                if ch == "Call":
                    secs = ((m.get("meta") or {}).get("call") or {}).get("duration") or 0
                    if secs:
                        k["min_" + (m.get("direction") or "none")] += math.ceil(secs / 60)
            cursor, pages = js.get("nextCursor"), pages + 1
            if stop or not cursor or not msgs:
                break
    print("| Month | Channel | In | Out | SMS segments out | Call mins in | Call mins out |")
    print("|---|---|---|---|---|---|---|")
    for (month, ch), k in sorted(rows.items()):
        print(f"| {month} | {ch} | {k['inbound']} | {k['outbound']} | "
              f"{k['segments_out'] or ''} | {k['min_inbound'] or ''} | {k['min_outbound'] or ''} |")


if __name__ == "__main__":
    main()
