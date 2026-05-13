"""External calendar (Outlook published ICS) → busy blocks.

Fetches Wes's published Outlook calendar and converts each "Busy" or
"Out of office" event into a TimeBlock that slots into availability.

Why ICS not Graph API:
  - Wes is a sole trader; Azure AD app registration + OAuth refresh is
    overkill.
  - The ICS feed is read-only and "obscurity-private" (URL contains a
    GUID). Treat the URL as a secret — env var only, never commit.
  - Outlook publishes the feed with ~3 hour lag. Fine for personal
    events which are usually planned days ahead; for last-minute
    blocks, Wes can still drop a manual SM8 jobactivity in.

What gets blocked:
  - Events where TRANSP=OPAQUE (default) AND
    X-MICROSOFT-CDO-BUSYSTATUS is BUSY or OOF.
  - "Free" and (by default) "Tentative" events are ignored.
  - Cancelled events are ignored.

Recurring events are expanded via `recurring_ical_events` since
Outlook's ICS includes RRULE definitions, not pre-expanded instances.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import recurring_ical_events
from icalendar import Calendar

from availability import TimeBlock

logger = logging.getLogger(__name__)

LOCAL_TZ = ZoneInfo("Europe/London")


def _to_local_naive(value: date | datetime) -> datetime:
    """Coerce ICS date/datetime values into local naive datetime.

    iCalendar uses two value types:
      - DATE   → an all-day event (e.g. "On holiday all day"). Becomes
                 midnight local on that calendar day.
      - DATETIME → may be tz-aware (with VTIMEZONE) or floating. We
                 convert to Europe/London and strip tzinfo so the
                 result can be compared with SM8's naive datetimes.
    """
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(LOCAL_TZ)
        return value.replace(tzinfo=None)
    # Plain date → midnight local
    return datetime.combine(value, datetime.min.time())


def _is_blocking_event(component) -> bool:
    """Decide whether a VEVENT counts as a busy block."""
    # Cancelled? Skip.
    if str(component.get("STATUS", "")).upper() == "CANCELLED":
        return False

    # TRANSP=TRANSPARENT means "doesn't block free/busy time"
    transp = str(component.get("TRANSP", "OPAQUE")).upper()
    if transp == "TRANSPARENT":
        return False

    # Outlook-specific: X-MICROSOFT-CDO-BUSYSTATUS overrides TRANSP
    # Values: FREE, TENTATIVE, BUSY, OOF (out of office), WORKINGELSEWHERE
    ms_busy = str(component.get("X-MICROSOFT-CDO-BUSYSTATUS", "BUSY")).upper()
    if ms_busy in {"FREE", "TENTATIVE"}:
        return False

    return True


async def fetch_ics_busy_blocks(
    ics_url: str,
    *,
    horizon_days: int = 60,
    now: datetime | None = None,
    timeout_s: float = 15.0,
) -> list[TimeBlock]:
    """Fetch the published ICS feed and return busy TimeBlocks in the
    window [now, now + horizon_days].

    Raises on network / parse errors — the caller should catch and
    fall back to "no external blocks" (better to over-show slots than
    fail the whole availability endpoint).
    """
    if now is None:
        now = datetime.now()
    horizon_end = now + timedelta(days=horizon_days)

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.get(ics_url)
        resp.raise_for_status()
        ics_bytes = resp.content

    cal = Calendar.from_ical(ics_bytes)

    # Expand recurrences inside the window (Outlook may include RRULE
    # definitions rather than pre-expanded occurrences for the full
    # 60-day horizon).
    expanded = recurring_ical_events.of(cal).between(now, horizon_end)

    blocks: list[TimeBlock] = []
    for component in expanded:
        if component.name != "VEVENT":
            continue
        if not _is_blocking_event(component):
            continue
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")
        if not dtstart or not dtend:
            continue

        start = _to_local_naive(dtstart.dt)
        end = _to_local_naive(dtend.dt)

        if end <= start:
            continue
        # Trim to horizon (recurring expansion may overrun slightly)
        if end < now or start > horizon_end:
            continue

        blocks.append(TimeBlock(start=start, end=end))

    logger.info(
        "ICS: fetched %d busy block(s) from external calendar (horizon=%d days)",
        len(blocks),
        horizon_days,
    )
    return blocks
