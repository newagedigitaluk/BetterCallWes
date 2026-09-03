"""Availability tests. Plain stdlib, no pytest: `python3 test_availability.py`.

Written when the booking form was found offering slots during personal
commitments. SM8 keeps blocked time in two separate stores and the diary is
only safe when both agree:

    jobactivity    booked jobs
    availability   personal/blocked time, including anything synced in from an
                   external calendar by the Calendar Import add-on, plus Staff
                   Leave and business closures

Reading only jobactivity was the bug.
"""
import sys
from datetime import date, datetime

from availability import (
    WorkingHours,
    free_slots,
    parse_availability_blocks,
    parse_busy_blocks,
    whole_day_slots,
)

STAFF = "staff-1"
HOURS = WorkingHours()
NOW = datetime(2026, 9, 7, 8, 0)  # a Monday, fixed so runs are reproducible

_failures: list[str] = []


def ok(cond: bool, msg: str) -> None:
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        _failures.append(msg)


def rec(**over):
    r = dict(
        active="1",
        regarding_object="staff",
        regarding_object_uuid=STAFF,
        availability_type="staff-busy-time",
        name="block",
        source=None,
    )
    r.update(over)
    return r


def starts(busy, duration_min=60, days=7):
    return [
        s.start
        for s in free_slots(
            duration_min=duration_min,
            days_ahead=days,
            busy=busy,
            hours=HOURS,
            now=NOW,
            today=date(2026, 9, 7),
        )
    ]


def main() -> int:
    # A short personal block removes only the slots it actually covers.
    busy = parse_availability_blocks(
        [rec(start_timestamp="2026-09-09 16:00:00", end_timestamp="2026-09-09 17:00:00")],
        STAFF,
    )
    s = starts(busy)
    ok(datetime(2026, 9, 9, 16, 0) not in s, "personal block removes the clashing slot")
    ok(datetime(2026, 9, 9, 9, 0) in s, "same day still bookable outside the block")

    # Multi-day leave clears every day it spans.
    busy = parse_availability_blocks(
        [rec(availability_type="staff-annual-leave",
             start_timestamp="2026-09-08 00:00:00",
             end_timestamp="2026-09-10 23:59:59")],
        STAFF,
    )
    s = starts(busy)
    ok(not any(x.date() in {date(2026, 9, 8), date(2026, 9, 9), date(2026, 9, 10)}
               for x in s), "multi-day leave clears every day it spans")
    ok(any(x.date() == date(2026, 9, 11) for x in s), "day after leave still bookable")

    # All-day event.
    busy = parse_availability_blocks(
        [rec(start_timestamp="2026-09-09 00:00:00", end_timestamp="2026-09-09 23:59:59")],
        STAFF,
    )
    ok(not any(x.date() == date(2026, 9, 9) for x in starts(busy)),
       "all-day event clears its day")

    # Scoping.
    ok(parse_availability_blocks(
        [rec(regarding_object_uuid="someone-else",
             start_timestamp="2026-09-09 09:00:00",
             end_timestamp="2026-09-09 17:00:00")], STAFF) == [],
       "another staff member's block is ignored")

    busy = parse_availability_blocks(
        [rec(regarding_object="vendor", regarding_object_uuid="vendor-1",
             availability_type="business-closed",
             start_timestamp="2026-09-09 00:00:00",
             end_timestamp="2026-09-09 23:59:59")], STAFF)
    ok(len(busy) == 1 and not any(x.date() == date(2026, 9, 9) for x in starts(busy)),
       "vendor-scoped business-closed blocks everyone")

    ok(parse_availability_blocks(
        [rec(active="0", start_timestamp="2026-09-09 09:00:00",
             end_timestamp="2026-09-09 17:00:00")], STAFF) == [],
       "inactive row is ignored")

    # Unknown types block rather than silently allowing a booking.
    ok(len(parse_availability_blocks(
        [rec(availability_type="staff-something-new",
             start_timestamp="2026-09-09 09:00:00",
             end_timestamp="2026-09-09 17:00:00")], STAFF)) == 1,
       "unknown availability_type still blocks")

    # Bad data must never take out the diary.
    ok(parse_availability_blocks([
        rec(start_timestamp="nonsense", end_timestamp="2026-09-09 17:00:00"),
        rec(start_timestamp="2026-09-09 17:00:00", end_timestamp="2026-09-09 09:00:00"),
        rec(start_timestamp=None, end_timestamp=None),
        rec(start_timestamp="0000-00-00 00:00:00", end_timestamp="0000-00-00 00:00:00"),
        {"active": "1"},
    ], STAFF) == [], "malformed, null and zero dates are dropped without raising")

    ok(parse_busy_blocks([{"active": "1", "activity_was_scheduled": "1",
                           "start_date": None, "end_date": None}]) == [],
       "jobactivity parser also survives null dates")

    # Whole-day services (Power Flush) must respect even a one-hour block.
    busy = parse_availability_blocks(
        [rec(start_timestamp="2026-09-09 16:00:00", end_timestamp="2026-09-09 17:00:00")],
        STAFF,
    )
    days = [x.start.date() for x in whole_day_slots(
        days_ahead=7, busy=busy, hours=HOURS, now=NOW,
        today=date(2026, 9, 7), whole_day_min_lead_days=1)]
    ok(date(2026, 9, 9) not in days,
       "a one-hour personal block removes the whole-day slot")

    print("\nFAILURES:", _failures if _failures else "none")
    return 1 if _failures else 0


if __name__ == "__main__":
    sys.exit(main())
