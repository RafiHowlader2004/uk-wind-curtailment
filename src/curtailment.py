"""Compute curtailed wind energy from Elexon balancing data.

A unit's output over time is piecewise-linear: each segment ramps from
`level_from` MW at `start` to `level_to` MW at `end`.

Two series matter:
    PN    - what the unit planned to generate
    BOAL  - what the system operator instructed instead

Curtailment is the energy in the gap between them, counted only while an
instruction is in force, and only where the instruction sits *below* the plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Segment:
    """A straight line of MW between two instants."""

    start: datetime
    end: datetime
    level_from: float
    level_to: float

    def level_at(self, t: datetime) -> float | None:
        """MW at time t, or None if t falls outside this segment."""
        if not (self.start <= t <= self.end):
            return None
        span = (self.end - self.start).total_seconds()
        if span <= 0:
            return self.level_from
        frac = (t - self.start).total_seconds() / span
        return self.level_from + frac * (self.level_to - self.level_from)


def level_at(segments: list[Segment], t: datetime) -> float | None:
    """MW across a series of segments, or None if none covers t."""
    for s in segments:
        level = s.level_at(t)
        if level is not None:
            return level
    return None


def curtailment_mwh(
    pn: list[Segment], boal: list[Segment], step_seconds: int = 60
) -> float:
    """Energy lost to instructed reductions, in MWh.

    Integrates max(planned - instructed, 0) over every instant an
    instruction applies, using midpoint sampling at `step_seconds`.
    """
    if not boal:
        return 0.0

    start = min(s.start for s in boal)
    end = max(s.end for s in boal)
    step = timedelta(seconds=step_seconds)
    hours_per_step = step_seconds / 3600

    total = 0.0
    t = start
    while t < end:
        midpoint = t + step / 2
        instructed = level_at(boal, midpoint)
        planned = level_at(pn, midpoint)
        if instructed is not None and planned is not None:
            gap = planned - instructed
            if gap > 0:
                total += gap * hours_per_step
        t += step

    return total


def parse_segments(rows: list[dict]) -> list[Segment]:
    """Turn Elexon PN or BOALF records into sorted Segments."""
    segments = [
        Segment(
            start=_parse_time(r["timeFrom"]),
            end=_parse_time(r["timeTo"]),
            level_from=float(r["levelFrom"]),
            level_to=float(r["levelTo"]),
        )
        for r in rows
    ]
    return sorted(segments, key=lambda s: s.start)


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
