"""Availability / free-slot calculation.

Given Wes's working hours (Mon-Fri 09:00-12:00 + 13:00-17:00, lunch break
12:00-13:00) and the list of existing scheduled activities from
ServiceM8, compute the free slots over the next N days that can fit a
job of a given duration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterator


@dataclass(frozen=True)
class TimeBlock:
    start: datetime
    end: datetime

    @property
    def duration_min(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)

    def overlaps(self, other: "TimeBlock") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class WorkingHours:
    days: tuple[str, ...] = ("Mon", "Tue", "Wed", "Thu", "Fri")
    morning_start: time = time(9, 0)
    morning_end: time = time(12, 0)
    afternoon_start: time = time(13, 0)
    afternoon_end: time = time(17, 0)

    _DAY_MAP = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

    def is_working_day(self, d: date) -> bool:
        return d.weekday() in {self._DAY_MAP[name] for name in self.days}

    def working_blocks(self, d: date) -> list[TimeBlock]:
        """Two blocks per working day: 9-12 and 13-17."""
        if not self.is_working_day(d):
            return []
        return [
            TimeBlock(
                start=datetime.combine(d, self.morning_start),
                end=datetime.combine(d, self.morning_end),
            ),
            TimeBlock(
                start=datetime.combine(d, self.afternoon_start),
                end=datetime.combine(d, self.afternoon_end),
            ),
        ]


def _parse_sm8_datetime(s: str) -> datetime:
    """SM8 returns 'YYYY-MM-DD HH:MM:SS' (no timezone — treat as local)."""
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")


def parse_busy_blocks(activities: list[dict]) -> list[TimeBlock]:
    """Turn raw SM8 jobactivity records into clean TimeBlocks.

    Filters for active records that were actually scheduled (not just
    casual time entries against a job).
    """
    blocks: list[TimeBlock] = []
    for a in activities:
        if a.get("active") not in ("1", 1, True):
            continue
        # activity_was_scheduled=1 means it's a real diary entry (not a
        # retroactive time log against a completed job).
        if a.get("activity_was_scheduled") not in ("1", 1, True):
            continue
        try:
            start = _parse_sm8_datetime(a["start_date"])
            end = _parse_sm8_datetime(a["end_date"])
        except (KeyError, ValueError):
            continue
        if end <= start:
            continue
        blocks.append(TimeBlock(start=start, end=end))
    return blocks


def free_slots(
    *,
    duration_min: int,
    days_ahead: int,
    busy: list[TimeBlock],
    hours: WorkingHours,
    today: date | None = None,
    step_min: int = 30,
    now: datetime | None = None,
    min_lead_time_hours: float = 0,
    same_day_cutoff_hour: int | None = None,
) -> Iterator[TimeBlock]:
    """Walk forward day by day, yielding free slots that fit duration_min.

    Args:
        step_min: how finely to step the start time within each working block.
                  30 mins gives "9:00, 9:30, 10:00..." starts.
        now: the current moment (defaults to datetime.now()). Used to enforce
             lead-time and same-day-cutoff rules. Override in tests.
        min_lead_time_hours: a slot's start must be at least this many hours
             after `now`. Applies to all days but in practice only filters
             today's earliest slots.
        same_day_cutoff_hour: if now.hour >= this value, no same-day slots are
             offered at all (Wes's day is too far gone to take more work).
             None disables the cutoff.
    """
    if now is None:
        now = datetime.now()
    if today is None:
        today = now.date()

    earliest = now + timedelta(hours=min_lead_time_hours)
    cutoff_skip_today = (
        same_day_cutoff_hour is not None and now.hour >= same_day_cutoff_hour
    )

    busy_sorted = sorted(busy, key=lambda b: b.start)

    for offset in range(days_ahead):
        d = today + timedelta(days=offset)
        if d == today and cutoff_skip_today:
            continue
        for work in hours.working_blocks(d):
            # Find busy blocks that intersect this working block
            relevant = [b for b in busy_sorted if b.overlaps(work)]
            cursor = work.start
            while cursor + timedelta(minutes=duration_min) <= work.end:
                proposed = TimeBlock(
                    start=cursor,
                    end=cursor + timedelta(minutes=duration_min),
                )
                if proposed.start >= earliest and not any(
                    proposed.overlaps(b) for b in relevant
                ):
                    yield proposed
                cursor += timedelta(minutes=step_min)


def whole_day_slots(
    *,
    days_ahead: int,
    busy: list[TimeBlock],
    hours: WorkingHours,
    today: date | None = None,
    now: datetime | None = None,
    whole_day_min_lead_days: int = 1,
) -> Iterator[TimeBlock]:
    """For full-day services (Power Flush). Yields one slot per fully-free workday.

    A day counts as free if no busy block overlaps either working window.

    Args:
        whole_day_min_lead_days: earliest offered day is `today + N days`.
             Default 1 means "no same-day whole-day bookings" — Power Flush
             needs prep so we never offer it for today.
    """
    if now is None:
        now = datetime.now()
    if today is None:
        today = now.date()
    busy_sorted = sorted(busy, key=lambda b: b.start)
    start_day = today + timedelta(days=max(0, whole_day_min_lead_days))
    for offset in range(days_ahead):
        d = start_day + timedelta(days=offset)
        blocks = hours.working_blocks(d)
        if not blocks:
            continue
        day_span = TimeBlock(start=blocks[0].start, end=blocks[-1].end)
        if not any(b.overlaps(day_span) for b in busy_sorted):
            yield day_span
